from participium import create_app


app = create_app()


def _local_url(host: str, port: int, path: str) -> str:
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    return f"http://{display_host}:{port}{path}"


if __name__ == "__main__":
    settings = app.config["SETTINGS"]
    print(f"Swagger UI: {_local_url(settings.host, settings.port, '/apidocs/')}", flush=True)
    app.run(host=settings.host, port=settings.port, debug=settings.debug, use_reloader=False)
