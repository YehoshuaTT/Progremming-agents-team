# Architecture Plan: User Profile Page

**Author:** Architect

## 1. System Architecture

The feature will be implemented using a standard client-server architecture.

- **Frontend:** A single-page application (SPA) built with Vite (React).
- **Backend:** A RESTful API service built with Python (Flask).
- **Database:** PostgreSQL for storing user data.

## 2. Data Model

**`users` table:**

| Column          | Type        | Constraints     |
|-----------------|-------------|-----------------|
| `id`            | `SERIAL`    | `PRIMARY KEY`   |
| `username`      | `VARCHAR(50)` | `UNIQUE, NOT NULL` |
| `email`         | `VARCHAR(100)`| `UNIQUE, NOT NULL` |
| `password_hash` | `VARCHAR(128)`| `NOT NULL`      |
| `profile_picture_url` | `VARCHAR(255)`|                 |
| `bio`           | `TEXT`      |                 |
| `created_at`    | `TIMESTAMP` | `DEFAULT NOW()` |

## 3. API Specification

- `GET /api/users/{userId}`
    - **Description:** Retrieves a user's profile.
    - **Response:** A JSON object with user data (excluding `password_hash`).
- `POST /api/users/{userId}`
    - **Description:** Updates a user's profile (bio, profile picture).
    - **Request Body:** A JSON object with the fields to update.
    - **Response:** The updated user object.

## 4. Deployment Plan

- **Frontend:** Deployed as a static site to a CDN (e.g., AWS S3/CloudFront).
- **Backend:** Deployed as a containerized application to a cloud platform (e.g., AWS ECS).
- **Database:** A managed PostgreSQL instance (e.g., AWS RDS).
