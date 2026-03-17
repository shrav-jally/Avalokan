# Avalokan Project Context

## Domain & Context
Avalokan is a sentiment analysis and summarization tool developed for the Ministry of Corporate Affairs (MCA). It is designed to handle the MCA eConsultation logic, facilitating the gathering, analysis, and management of public and stakeholder feedback on government policies.

## Core Data Entities
The system revolves around three core data entities:

1. **Policy (The Parent):** The overarching regulatory or legislative initiative. This acts as the container for all subsequent drafts and iterations.
2. **Draft (The Versioned Document):** A specific version or iteration of a Policy released for public consultation. A Policy can have multiple Drafts over time as it evolves.
3. **Comments (The Stakeholder Feedback):** The individual submissions, feedback, and sentiment provided by stakeholders on a specific Draft.

## Core Rules & Logic
- **Multi-versioning:** All logic within the application MUST support multi-versioning. When a new Draft version of a Policy is released, it automatically supersedes the previous one. Analytics, visualizations, and tracking must respect this version lineage and allow for comparisons across versions.
