import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="::", port=8000, reload=True, reload_dirs=["app"])
