<!-- 
  ╔══════════════════════════════════════════════════════════════╗
  ║   NexCart — Production‑grade Backend E‑Commerce API         ║
  ║   Clean Architecture · Service Layer · Repository Pattern   ║
  ╚══════════════════════════════════════════════════════════════╝
-->

<div align="center">

# 🛒 NexCart

**Scalable, production‑ready REST API for e‑commerce**  
*Built with Django REST Framework using Clean Architecture and Service Layer principles*

[![Python](https://img.shields.io/badge/python-3.13-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.0-092e20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/django_rest_framework-3.15-red?logo=django)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-16-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/docker-ready-2496ed?logo=docker&logoColor=white)](https://www.docker.com/)
[![Coverage](https://img.shields.io/badge/coverage-81%25-brightgreen?logo=pytest)](https://github.com/your-username/nexcart)
[![Tests](https://img.shields.io/badge/tests-67_passed-success?logo=githubactions)](https://github.com/your-username/nexcart/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

</div>

---

## 📑 Table of Contents

- [Project Overview](#-project-overview)
- [Architecture](#-architecture)
- [Folder Structure](#-folder-structure)
- [Technology Stack](#-technology-stack)
- [Features](#-features)
- [API Overview](#-api-overview)
- [Authentication Flow](#-authentication-flow)
- [Database Design Overview](#-database-design-overview)
- [Installation](#-installation)
- [Local Development](#-local-development)
- [Docker](#-docker)
- [Environment Variables](#-environment-variables)
- [Running Tests](#-running-tests)
- [Swagger Documentation](#-swagger-documentation)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Deployment](#-deployment)
- [Security Features](#-security-features)
- [Performance Considerations](#-performance-considerations)
- [Design Patterns Used](#-design-patterns-used)
- [Project Statistics](#-project-statistics)
- [Roadmap](#-roadmap)
- [Future Improvements](#-future-improvements)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)

---

## 🧠 Project Overview

NexCart is a **backend‑only** e‑commerce platform designed to serve any frontend (mobile, web, PWA) through a versioned REST API. The codebase follows **Clean Architecture** with a strict **Service Layer** and **Repository Pattern** – every business rule lives in services, and data access is abstracted behind repositories. Views are kept thin, serializers handle validation, and the domain logic is completely decoupled from the framework.

> **Why NexCart?**  
> Most Django e‑commerce projects mix business logic with views or models, making them hard to test, maintain, or extend. NexCart demonstrates how a real‑world backend can be built with the same architectural rigour you’d expect from a Senior Backend Engineer – fully tested, dockerised, and ready for production.

The repository contains **no frontend code** – only the API and its supporting infrastructure (Celery, Redis, PostgreSQL, Nginx, etc.).

---

## 🏗 Architecture

NexCart enforces a clear separation of concerns. The dependency rule points inward: controllers (views) depend on services, services depend on repositories, and repositories depend on models. External integrations (payments, email) are abstracted behind interfaces.

```mermaid
graph TD
    Client[Client / Frontend] --> Nginx
    Nginx --> Gunicorn
    Gunicorn --> DjangoApp[Django Application]

    subgraph Django Application
        direction TB
        Views[Thin Views / APIViews] --> Services[Service Layer]
        Services --> Repositories[Repository Layer]
        Repositories --> Models[Django ORM Models]
        Serializers[Serializers / Validation]
        Views --> Serializers
    end

    DjangoApp --> PostgreSQL[(PostgreSQL)]
    DjangoApp --> Redis[(Redis)]
    Redis --> CeleryWorker[Celery Worker]
    CeleryWorker --> DjangoApp
    CeleryWorker --> EmailService[Email Service]