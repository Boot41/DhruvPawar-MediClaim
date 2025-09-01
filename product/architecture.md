# MedClaim AI - Database Schema Architecture

This document provides a visual representation of the database schema for the MedClaim AI platform. The diagram below illustrates the tables, their fields, and the relationships between them.

## Entity-Relationship Diagram (ERD)

The following ERD is generated using Mermaid syntax and shows the logical structure of the database.

```mermaid
erDiagram
    users {
        UUID id PK
        string email
        string phone
        string first_name
        string last_name
        date date_of_birth
        text address
        UserRole role
        boolean is_active
        string password_hash
        datetime last_login
        datetime created_at
        datetime updated_at
    }

    insurance_providers {
        UUID id PK
        string name
        string code
        string contact_email
        string contact_phone
        text address
        string api_endpoint
        boolean is_active
        datetime created_at
    }

    insurance_policies {
        UUID id PK
        UUID user_id FK
        UUID provider_id FK
        string policy_number
        string group_number
        string policy_type
        date coverage_start_date
        date coverage_end_date
        decimal annual_deductible
        decimal annual_out_of_pocket_max
        decimal copay_amount
        float coverage_percentage
        boolean is_active
        json policy_details
        datetime created_at
    }

    healthcare_providers {
        UUID id PK
        string name
        string npi_number
        string specialty
        text address
        string phone
        string email
        string tax_id
        boolean is_active
        datetime created_at
    }

    documents {
        UUID id PK
        UUID user_id FK
        UUID claim_id FK
        string filename
        string original_filename
        string file_path
        int file_size
        string mime_type
        DocumentType document_type
        json extracted_data
        float extraction_confidence
        boolean is_processed
        boolean is_verified
        string upload_source
        datetime created_at
        datetime updated_at
    }

    claims {
        UUID id PK
        string claim_number
        UUID user_id FK
        UUID policy_id FK
        UUID healthcare_provider_id FK
        ClaimStatus status
        string claim_type
        string diagnosis_code
        text diagnosis_description
        date date_of_service_start
        date date_of_service_end
        datetime submission_date
        datetime decision_date
        decimal total_billed_amount
        decimal total_allowed_amount
        decimal insurance_paid_amount
        decimal patient_responsibility
        decimal deductible_applied
        decimal copay_applied
        decimal coinsurance_applied
        string processed_by
        text denial_reason
        text notes
        string external_claim_id
        decimal ai_estimated_coverage
        decimal ai_estimated_patient_cost
        float ai_confidence_score
        datetime created_at
        datetime updated_at
    }

    medical_services {
        UUID id PK
        UUID claim_id FK
        UUID provider_id FK
        string service_code
        text service_description
        date service_date
        int quantity
        decimal unit_price
        decimal total_charge
        decimal allowed_amount
        decimal paid_amount
        text denial_reason
        datetime created_at
    }

    claim_status_history {
        UUID id PK
        UUID claim_id FK
        ClaimStatus old_status
        ClaimStatus new_status
        string changed_by
        text change_reason
        text notes
        datetime created_at
    }

    payments {
        UUID id PK
        UUID claim_id FK
        string payment_type
        decimal amount
        date payment_date
        string payment_method
        string reference_number
        PaymentStatus status
        text notes
        datetime created_at
    }

    conversation_messages {
        UUID id PK
        UUID user_id FK
        UUID claim_id FK
        string session_id
        string role
        string message_type
        text content
        json metadata
        UUID parent_message_id FK
        boolean is_flagged
        datetime created_at
    }

    processing_jobs {
        UUID id PK
        string job_type
        UUID entity_id
        string entity_type
        string status
        json input_data
        json output_data
        text error_message
        datetime started_at
        datetime completed_at
        datetime created_at
    }

    audit_logs {
        UUID id PK
        UUID user_id FK
        string action
        string entity_type
        UUID entity_id
        json old_values
        json new_values
        string ip_address
        text user_agent
        datetime created_at
    }

    system_config {
        UUID id PK
        string config_key
        json config_value
        text description
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    users ||--o{ insurance_policies : "has"
    users ||--o{ claims : "has"
    users ||--o{ documents : "has"
    users ||--o{ conversation_messages : "has"
    users ||--o{ audit_logs : "has"

    insurance_providers ||--o{ insurance_policies : "has"

    insurance_policies }o--|| claims : "covers"

    healthcare_providers ||--o{ claims : "provides for"
    healthcare_providers ||--o{ medical_services : "provides"

    claims ||--o{ documents : "related to"
    claims ||--o{ medical_services : "contains"
    claims ||--o{ claim_status_history : "has history of"
    claims ||--o{ payments : "has"
    claims ||--o{ conversation_messages : "context for"

    conversation_messages }o--o| conversation_messages : "replies to"
```

## Table Descriptions and Relationships

### Core Tables

*   **users**: Stores user information, including customers, agents, and administrators. This is the central entity for user management.
*   **claims**: Represents an insurance claim, which is the core business entity. It links together the user, their policy, healthcare services, and associated documents.
*   **documents**: Manages all uploaded files, linking them to users and, optionally, to specific claims.

### Insurance and Healthcare

*   **insurance_providers**: A list of insurance companies.
*   **insurance_policies**: Details of a user's insurance plan with a specific provider.
*   **healthcare_providers**: Information about medical facilities and practitioners (hospitals, clinics, doctors).
*   **medical_services**: Line items on a claim, detailing specific procedures, services, or medications.

### Supporting Tables

*   **claim_status_history**: An audit trail for all status changes a claim goes through.
*   **payments**: Tracks financial transactions related to a claim.
*   **conversation_messages**: Stores chat interactions between users and the AI assistant.

### System and Auditing

*   **processing_jobs**: A queue for managing asynchronous background tasks like AI document analysis.
*   **audit_logs**: Records significant actions performed by users for security and compliance.
*   **system_config**: A key-value store for application-wide settings.

## Foreign Key Relationships

*   `insurance_policies.user_id` -> `users.id`
*   `insurance_policies.provider_id` -> `insurance_providers.id`
*   `claims.user_id` -> `users.id`
*   `claims.policy_id` -> `insurance_policies.id`
*   `claims.healthcare_provider_id` -> `healthcare_providers.id`
*   `documents.user_id` -> `users.id`
*   `documents.claim_id` -> `claims.id`
*   `medical_services.claim_id` -> `claims.id`
*   `medical_services.provider_id` -> `healthcare_providers.id`
*   `claim_status_history.claim_id` -> `claims.id`
*   `payments.claim_id` -> `claims.id`
*   `conversation_messages.user_id` -> `users.id`
*   `conversation_messages.claim_id` -> `claims.id`
*   `conversation_messages.parent_message_id` -> `conversation_messages.id`
*   `audit_logs.user_id` -> `users.id`
# MedClaim AI - Database Schema Architecture

This document provides a visual representation of the database schema for the MedClaim AI platform using Markdown tables.

---

### **`users`**

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Primary Key |
| `email` | string | | User's email address |
| `phone` | string | | User's phone number |
| `first_name` | string | | User's first name |
| `last_name` | string | | User's last name |
| `date_of_birth` | date | | User's date of birth |
| `address` | text | | User's physical address |
| `role` | UserRole | | User's role (admin, agent, customer) |
| `is_active` | boolean | | Flag for active users |
| `password_hash` | string | | Hashed password |
| `last_login` | datetime | | Timestamp of the last login |
| `created_at` | datetime | | Timestamp of creation |
| `updated_at` | datetime | | Timestamp of last update |

---

### **`insurance_providers`**

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Primary Key |
| `name` | string | | Name of the insurance company |
| `code` | string | | Unique code for the provider |
| `contact_email` | string | | Contact email |
| `contact_phone` | string | | Contact phone number |
| `address` | text | | Provider's address |
| `api_endpoint` | string | | API endpoint for integration |
| `is_active` | boolean | | Flag for active providers |
| `created_at` | datetime | | Timestamp of creation |

---

### **`insurance_policies`**

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Primary Key |
| `user_id` | UUID | FK | Foreign Key to `users.id` |
| `provider_id` | UUID | FK | Foreign Key to `insurance_providers.id` |
| `policy_number`| string | | Unique policy number |
| `policy_type` | string | | Type of policy (e.g., PPO, HMO) |
| `coverage_start_date`| date | | Policy start date |
| `coverage_end_date`| date | | Policy end date |
| `is_active` | boolean | | Flag for active policies |

---

### **`claims`**

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK | Primary Key |
| `claim_number` | string | | Unique claim identifier |
| `user_id` | UUID | FK | Foreign Key to `users.id` |
| `policy_id` | UUID | FK | Foreign Key to `insurance_policies.id` |
| `status` | ClaimStatus | | Current status of the claim |
| `total_billed_amount` | decimal | | Total amount billed by provider |
| `insurance_paid_amount` | decimal | | Amount paid by insurance |
| `patient_responsibility`| decimal | | Amount owed by the patient |
| `submission_date`| datetime | | Date the claim was submitted |

---

## Relationships

- `users` (1) -- (many) `insurance_policies`
- `users` (1) -- (many) `claims`
- `users` (1) -- (many) `documents`
- `insurance_providers` (1) -- (many) `insurance_policies`
- `insurance_policies` (1) -- (many) `claims`
- `claims` (1) -- (many) `documents`
- `claims` (1) -- (many) `medical_services`
- `claims` (1) -- (many) `payments`
