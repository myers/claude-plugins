# Database Patterns

## Connection Pooling

Use psycopg's built-in connection pooling instead of Django's `CONN_MAX_AGE`:

```python
# Enable psycopg connection pooling
if db_from_env.get("ENGINE") == "django.db.backends.postgresql":
    db_from_env["OPTIONS"] = db_from_env.get("OPTIONS", {})
    db_from_env["OPTIONS"]["pool"] = True
    db_from_env.pop("CONN_MAX_AGE", None)  # Incompatible with pooling
```

---

## NOT EXISTS Pattern

Use `~Exists()` instead of `exclude()` with JOINs:

```python
def filter_unread(queryset, user):
    seen_subquery = Seen.objects.filter(post=OuterRef("pk"), user=user)
    return queryset.filter(~Exists(seen_subquery))  # NOT EXISTS
```

---

## Subquery to Avoid Duplicates

Use `Subquery` instead of joins that can create duplicates:

```python
def with_user_like(self, user):
    like_subquery = Like.objects.filter(
        post=OuterRef("pk"), user=user
    ).values("created")[:1]
    return self.annotate(like_created=Subquery(like_subquery))
```

---

## Cursor Pagination

Use cursor pagination instead of offset-limit for large datasets:

```python
# Using django-cursor-pagination
from cursor_pagination import CursorPaginator

def get_cursor_paginated_page(queryset, request, ordering=("-posted_at", "-pk")):
    paginator = CursorPaginator(queryset, ordering=ordering)
    cursor = request.GET.get("cursor")
    return paginator.page(cursor=cursor)
```

---

## Sophisticated Indexing

```python
class Post(models.Model):
    class Meta:
        indexes = [
            # Full-text search
            GinIndex(fields=["search_vector"]),

            # Cursor pagination
            models.Index(fields=["-posted_at", "-id"]),

            # Partial index for filtered queries
            models.Index(
                F("posted_at").desc(nulls_last=True),
                F("id").desc(nulls_last=True),
                name="posts_post_visible_posted",
                condition=Q(hidden=False, missing_files=False),
            ),
        ]
```

---

## Raw SQL When Needed

Don't fight the ORM for complex queries:

```python
class SourceManager(models.Manager):
    def by_recent_post(self, limit=25, offset=0):
        return self.raw("""
            SELECT s.*, p.post_count, p.latest_post_created_at
            FROM posts_source s
            CROSS JOIN LATERAL (
                SELECT COUNT(*) as post_count,
                       MAX(created_at) as latest_post_created_at
                FROM posts_post
                WHERE source_id = s.id
            ) p
            WHERE p.post_count > 0
            ORDER BY p.latest_post_created_at DESC NULLS LAST
            LIMIT %s OFFSET %s
        """, [limit, offset])
```
