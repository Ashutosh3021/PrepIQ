import uvicorn
import sys

if __name__ == "__main__":
    sys.path.insert(0, "C:/Users/ashut/Downloads/FinishedP/PrepIQ/backend")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)
