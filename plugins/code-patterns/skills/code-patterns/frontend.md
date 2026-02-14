# Frontend Integration

## Hotwired (Turbo + Stimulus)

- Use Turbo Drive for navigation
- Turbo Frames for partial page updates
- Turbo Streams for real-time updates
- Stimulus controllers for JavaScript behavior

---

## Vite for Asset Bundling

```python
# settings.py
DJANGO_VITE = {
    "default": {
        "dev_mode": DEBUG,
        "dev_server_host": "localhost",
        "dev_server_port": int(os.getenv("VITE_PORT", "8601")),
        "manifest_path": os.path.join(BASE_DIR, "assets", "dist", ".vite", "manifest.json"),
    }
}
```
