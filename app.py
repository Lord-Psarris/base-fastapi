from fastapi.openapi.docs import get_swagger_ui_oauth2_redirect_html, get_swagger_ui_html
from utils.app_handler import create_app

app = create_app(title='Base API', docs_url=None)


# default route
@app.get('/')
def home():
    return 'welcome to a base api'


# loading up custom docs
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger/swagger-ui.css",
        swagger_favicon_url="/static/assets/logo.png"
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


if __name__ == "__main__":
    import uvicorn
    import configs

    uvicorn.run("app:app", port=8000, reload=configs.DEBUG_MODE)
