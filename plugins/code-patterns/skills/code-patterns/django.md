# Django Patterns

## Project Structure

### Architecture Philosophy

- **Skinny models**: Models only contain what's needed to store data in the database
- **Skinny views**: Views delegate to services and filters
- **Skinny management commands**: Commands handle CLI parsing and orchestration, delegate to services
- **Fat services**: Business logic lives in dedicated service modules

### Directory Layout

```
project/
├── bin/                    # Shell wrapper scripts
├── web/                    # Django project config (settings, urls, wsgi/rsgi)
├── posts/                  # Main app
│   ├── management/commands/
│   ├── services/           # Business logic
│   ├── tests/
│   │   ├── conftest.py     # App-specific fixtures
│   │   ├── factories.py    # Factory-boy factories
│   │   └── test_*.py
│   └── views/
│       ├── __init__.py
│       └── filters.py      # Composable filter functions
├── templates/
├── assets/                 # Frontend source files
├── conftest.py             # Root pytest config
└── pyproject.toml
```

### Service Layer

Business logic lives in `app/services/`:

```python
# posts/services/html_processing.py
def clean_html(html: str) -> str:
    """Pure function for HTML cleaning."""
    ...

def process_post_html(post: Post, urls: dict[str, str]) -> str:
    """Orchestrates HTML processing for a post."""
    ...
```

---

## Settings Configuration

### Environment-Based Configuration

```python
# web/settings.py
from dotenv import load_dotenv
load_dotenv()

# Development vs Production
if os.getenv("DJANGO_ENV", "development") == "development":
    DEBUG = True
else:
    DEBUG = False
```

### PostgreSQL-Only

Enforce PostgreSQL as the only supported database:

```python
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError(
        "DATABASE_URL environment variable is required. "
        "This project only supports PostgreSQL."
    )
```

### Long Session Cookies

For apps where users stay logged in:

```python
# 20 years in seconds
SESSION_COOKIE_AGE = 60 * 60 * 24 * 365 * 20
```

### Pillow Robustness

Handle corrupted/truncated images gracefully:

```python
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = 200_000_000
```

---

## Authentication

### Global Login Required (Secure by Default)

Use Django's `LoginRequiredMiddleware` to require authentication on ALL views by default:

```python
MIDDLEWARE = [
    # ... other middleware
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
]
```

To make a view publicly accessible, explicitly opt-out:

```python
from django.contrib.auth.decorators import login_not_required

@login_not_required
def public_view(request):
    ...
```

**Rationale**: This inverts the responsibility model. Instead of remembering to add `@login_required` everywhere (and risking accidental exposure), you must explicitly mark views as public.

---

## Model Patterns

### Custom QuerySet Methods

```python
class PostQuerySet(models.QuerySet):
    def with_user_like(self, user):
        """Annotate posts with user's like timestamp using Subquery to avoid duplicates."""
        like_subquery = Like.objects.filter(
            post=OuterRef("pk"), user=user
        ).values("created")[:1]
        return self.annotate(like_created=Subquery(like_subquery))


class Post(models.Model):
    objects = PostQuerySet.as_manager()
```

### Validation in save()

Always call `full_clean()` in `save()` to ensure validation runs:

```python
class Source(models.Model):
    def clean(self):
        # Auto-populate name from URL
        if not self.name and self.url:
            self.name = extract_subdomain(self.url)

    def save(self, *args, **kwargs):
        self.full_clean()  # Always validate
        super().save(*args, **kwargs)
```

---

## View Patterns

### Function-Based Views

Prefer FBV over CBV for simplicity:

```python
@require_POST
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    Like.objects.get_or_create(user=request.user, post=post)
    return redirect(post)
```

### Composable Filter Functions

Instead of filter classes, use simple functions:

```python
# posts/views/filters.py
def filter_base(queryset):
    """Base filter for posts."""
    return queryset.filter(hidden=False, missing_files=False)

def filter_favorites(queryset, user):
    """Filter to only user's favorite posts."""
    return queryset.filter(like__user=user)

def filter_unread(queryset, user):
    """Filter to only unread posts using NOT EXISTS."""
    seen_subquery = Seen.objects.filter(post=OuterRef("pk"), user=user)
    return queryset.filter(~Exists(seen_subquery))

def filter_search(queryset, query):
    """Filter by search query. Returns (queryset, error_message)."""
    if not query:
        return queryset, None
    # ... implementation
```

Usage in views:

```python
def post_list(request, source_name=None, tag_slug=None):
    queryset = Post.objects.all()
    queryset = filter_base(queryset)

    if source_name:
        queryset = filter_source(queryset, source_name)
    if tag_slug:
        queryset = filter_tag(queryset, tag_slug)
    if request.GET.get("unread"):
        queryset = filter_unread(queryset, request.user)
    # ...
```

### Turbo Stream Support

Support both HTML and Turbo Stream responses (see also [frontend.md](frontend.md) for Hotwired patterns):

```python
from django.views.decorators.vary import vary_on_headers

@vary_on_headers("Accept")
def post_list(request, **kwargs):
    # Template resolution:
    # - Accept: text/vnd.turbo-stream.html -> post_list.turbo-stream.html
    # - Default -> post_list.html
    ...
```

---

## Management Command Patterns

### Skinny Commands

Management commands should handle CLI parsing, validation, and orchestration only. Business logic belongs in services or dedicated modules.

**Good: Skinny command that delegates to a service**

```python
# myapp/management/commands/update_cookies.py
class Command(BaseCommand):
    help = "Update cookies from various input formats"

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--from-curl", help="Parse cookies from a curl command")
        group.add_argument("--from-browser", help="Parse cookies from browser format")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        # Parse input (command responsibility)
        if options["from_curl"]:
            cookies = self.parse_curl_cookies(options["from_curl"])
        elif options["from_browser"]:
            cookies = self.parse_browser_cookies(options["from_browser"])

        if not cookies:
            raise CommandError("No cookies found in input")

        # Display (command responsibility)
        self.stdout.write(f"Found {len(cookies)} cookies:")
        for key, value in cookies.items():
            self.stdout.write(f"  {key}: {value[:20]}...")

        if options["dry_run"]:
            return

        # Delegate to service (business logic lives elsewhere)
        from myapp.services.cookies import save_cookies
        success = save_cookies(cookies)

        if success:
            self.stdout.write(self.style.SUCCESS("Updated cookies"))
```

### Minimal Worker Commands

Queue workers should be trivial - just configuration:

```python
# posts/management/commands/worker.py
from pgq.commands import Worker
from posts.queues import media_processing_queue

class Command(Worker):
    help = "Process media analysis tasks"
    queue = media_processing_queue
    # That's it. 5 lines total.
```

### Commands as Orchestrators

For complex operations, commands orchestrate but don't implement:

```python
# myapp/management/commands/capture_pages.py
class Command(BaseCommand):
    def handle(self, *args, **options):
        site = options["site"]

        # Get dependencies from services
        cookie = self.get_session_cookie()  # Calls service

        # Orchestrate steps (high-level flow)
        page_urls = self.capture_archive_page(site, cookie)
        self.capture_detail_pages(site, page_urls[:options["max_pages"]], cookie)
        self.capture_pagination(site, cookie)
        self.capture_edge_cases(site, cookie)

        self.stdout.write(self.style.SUCCESS("Done"))

    def get_session_cookie(self):
        # Delegate to service
        from myapp.services.cookies import get_cookies
        cookie = get_cookies()
        if not cookie:
            raise CommandError("No cookie found")
        return cookie
```

### Command Responsibilities

**Commands SHOULD handle:**

- Argument parsing (`add_arguments`)
- Input validation and error messages
- User output (`self.stdout.write`, `self.style.SUCCESS`)
- Orchestration flow (what order things happen)
- Progress indication

**Commands should NOT contain:**

- Business logic that could be reused elsewhere
- Complex data transformations
- Database queries beyond simple lookups
- Anything that should be testable in isolation

---

## Testing Patterns

### pytest-style Tests (No Classes)

All tests are standalone functions, not `django.test.TestCase` classes:

```python
# posts/tests/test_views.py
def test_post_list_requires_login(client):
    response = client.get("/posts/")
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


def test_post_list_shows_posts(authenticated_client, post):
    response = authenticated_client.get("/posts/")
    assert response.status_code == 200
    assert post.body in response.content.decode()
```

**Rationale**: Works better with pytest-xdist parallel execution and avoids database connection issues.

### Test File Location Convention

- Code at `appname/views.py` → tests at `appname/tests/test_views.py`
- Code at `appname/services/something.py` → tests at `appname/tests/services/test_something.py`

### Factory-Boy Factories

```python
# posts/tests/factories.py
class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post
        skip_postgeneration_save = True  # Tags don't need re-save

    source = factory.SubFactory(SourceFactory)
    posted_at = factory.Faker("date_time_this_year", tzinfo=zoneinfo.ZoneInfo("UTC"))
    body = factory.Faker("paragraph")
    original_url = factory.LazyAttribute(
        lambda o: f"{o.source.url}/post/{o.original_post_id}"
    )

    class Params:
        is_hidden = factory.Trait(hidden=True)
        recent = factory.Trait(posted_at=factory.LazyFunction(lambda: timezone.now()))
```

### Root conftest.py

```python
# conftest.py
import pytest
from django.db import connections

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """All tests get database access automatically."""
    pass

@pytest.fixture(autouse=True)
def close_db_connections_after_test():
    """Prevent race conditions in parallel test execution."""
    yield
    for conn in connections.all():
        conn.close()
```

### App-Specific Fixtures

```python
# posts/tests/conftest.py
@pytest.fixture
def authenticated_client(client, user):
    """Return a client with authenticated user."""
    client.force_login(user)
    return client

@pytest.fixture
def posts_batch(source):
    """Create multiple posts for testing pagination."""
    return [PostFactory(source=source) for _ in range(15)]
```

### Parallel Test Execution

```bash
# bin/test
exec uv run pytest -n auto "$@"
```

---

## Background Tasks

### django-pg-queue

```python
# posts/queues.py
from pgq import AtLeastOnceQueue

media_processing_queue = AtLeastOnceQueue(
    tasks={},
    queue="media_analysis",
    notify_channel="media_analysis",
)

# posts/tasks.py
from pgq import task
from posts.queues import media_processing_queue

@task(media_processing_queue)
def create_avif_from_gif(queue, job, args, meta):
    ...
```

### Signal-Driven Task Queueing

```python
# posts/signals.py
from django.db import transaction

@receiver(indexedfile_added)
def queue_media_processing(sender, indexed_file, **kwargs):
    def enqueue():
        from posts.tasks import process_media
        process_media.enqueue({"file_id": indexed_file.id})

    transaction.on_commit(enqueue)  # Only enqueue after commit succeeds
```

---

## Deployment

### RSGI Instead of WSGI

Use `django-rsgi` with Granian for better async performance:

```python
# web/rsgi.py
from django_rsgi import get_rsgi_application
application = get_rsgi_application()
```

### Version Info Context Processor

Track deployment info in templates:

```python
# myapp/context_processors.py
def version_info(request):
    return {
        "GIT_COMMIT": os.environ.get("GIT_COMMIT", "dev"),
        "GIT_BRANCH": os.environ.get("GIT_BRANCH", "local"),
        "BUILD_DATE": os.environ.get("BUILD_DATE", ""),
    }
```
