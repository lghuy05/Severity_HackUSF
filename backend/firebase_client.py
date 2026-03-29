"""Firebase Firestore database connection and utilities"""

import json
import logging
from pathlib import Path
from typing import Any

import firebase_admin
from firebase_admin import credentials, firestore


logger = logging.getLogger(__name__)

# Path to service account key
FIREBASE_KEY_PATH = Path(__file__).parent.parent / "firebase-key.json"


def init_firebase() -> Any:
    """
    Initialize Firebase Admin SDK and return Firestore client.
    
    Returns:
        Firestore client instance
        
    Raises:
        FileNotFoundError: If firebase-key.json not found
        Exception: If Firebase initialization fails
    """
    if not FIREBASE_KEY_PATH.exists():
        raise FileNotFoundError(
            f"Firebase key not found at {FIREBASE_KEY_PATH}. "
            "Please add firebase-key.json with your service account credentials."
        )
    
    # Initialize Firebase Admin SDK if not already initialized
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(str(FIREBASE_KEY_PATH))
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise
    
    return firestore.client()


def get_firestore_client() -> Any:
    """Get or create Firestore client"""
    try:
        if firebase_admin._apps:
            return firestore.client()
        return init_firebase()
    except Exception as e:
        logger.error(f"Error getting Firestore client: {e}")
        raise


def get_hospitals(location: str | None = None) -> list[dict]:
    """
    Fetch hospitals from Firestore.
    
    Args:
        location: Filter by location (optional)
        
    Returns:
        List of hospital documents
    """
    try:
        db = get_firestore_client()
        query = db.collection("hospitals")
        
        if location:
            query = query.where("location", "==", location)
        
        docs = query.stream()
        hospitals = []
        for doc in docs:
            hospital = doc.to_dict()
            hospital["id"] = doc.id
            hospitals.append(hospital)
        
        logger.info(f"Fetched {len(hospitals)} hospitals")
        return hospitals
    except Exception as e:
        logger.error(f"Error fetching hospitals from Firestore: {e}")
        return []


def get_patient(patient_id: str) -> dict | None:
    """
    Fetch patient record from Firestore.
    
    Args:
        patient_id: Patient document ID
        
    Returns:
        Patient document data or None if not found
    """
    try:
        db = get_firestore_client()
        doc = db.collection("patients").document(patient_id).get()
        
        if doc.exists:
            patient = doc.to_dict()
            patient["id"] = doc.id
            return patient
        return None
    except Exception as e:
        logger.error(f"Error fetching patient {patient_id}: {e}")
        return None


def save_appointment(appointment_data: dict) -> str:
    """
    Save appointment to Firestore.
    
    Args:
        appointment_data: Appointment details
        
    Returns:
        Appointment document ID
    """
    try:
        db = get_firestore_client()
        doc_ref = db.collection("appointments").add(appointment_data)
        appointment_id = doc_ref[1].id
        logger.info(f"Saved appointment: {appointment_id}")
        return appointment_id
    except Exception as e:
        logger.error(f"Error saving appointment: {e}")
        raise
