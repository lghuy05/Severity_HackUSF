from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any


class FirebaseConfigError(RuntimeError):
    pass


def _load_firebase_admin() -> tuple[Any, Any, Any, Any]:
    try:
        import firebase_admin
        from firebase_admin import auth, credentials, firestore
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on environment
        raise FirebaseConfigError(
            "firebase-admin is not installed. Run `pip install -r backend/requirements.txt`."
        ) from exc

    return firebase_admin, credentials, auth, firestore


def _firebase_project_id() -> str | None:
    return os.getenv("FIREBASE_PROJECT_ID") or os.getenv("NEXT_PUBLIC_FIREBASE_PROJECT_ID")


def _firebase_credentials() -> Any:
    _, credentials, _, _ = _load_firebase_admin()

    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if service_account_json:
        try:
            return credentials.Certificate(json.loads(service_account_json))
        except json.JSONDecodeError as exc:
            raise FirebaseConfigError("FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON.") from exc

    service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if service_account_path:
        return credentials.Certificate(service_account_path)

    google_application_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if google_application_credentials:
        return credentials.Certificate(google_application_credentials)

    return credentials.ApplicationDefault()


@lru_cache(maxsize=1)
def get_firebase_app() -> Any:
    firebase_admin, _, _, _ = _load_firebase_admin()

    if firebase_admin._apps:
        return firebase_admin.get_app()

    options: dict[str, str] = {}
    project_id = _firebase_project_id()
    if project_id:
        options["projectId"] = project_id

    try:
        return firebase_admin.initialize_app(_firebase_credentials(), options or None)
    except Exception as exc:  # pragma: no cover - external SDK behavior
        raise FirebaseConfigError(f"Unable to initialize Firebase Admin SDK: {exc}") from exc


def firebase_backend_ready() -> bool:
    try:
        get_firebase_app()
        return True
    except FirebaseConfigError:
        return False


def get_firestore_client() -> Any:
    _, _, _, firestore = _load_firebase_admin()
    try:
        return firestore.client(app=get_firebase_app())
    except Exception as exc:  # pragma: no cover - external SDK behavior
        raise FirebaseConfigError(f"Unable to initialize Firestore client: {exc}") from exc


def verify_firebase_token(id_token: str) -> dict[str, Any]:
    _, _, auth, _ = _load_firebase_admin()
    try:
        return auth.verify_id_token(id_token, app=get_firebase_app())
    except Exception as exc:  # pragma: no cover - external SDK behavior
        raise FirebaseConfigError(f"Unable to verify Firebase token: {exc}") from exc
