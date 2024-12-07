# Project Management API Documentation

## Overview
This API provides a comprehensive set of endpoints for managing projects, tasks, documents, and team collaboration features including forums and discussions.

## Authentication
All endpoints require authentication using JWT tokens. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## Projects Endpoints

### Project Management

#### List Projects
```http
GET /api/projects/
```
- Supports filtering by: status, location
- Supports search on: title, description, objectives, reference_number
- Supports ordering by: created_at, deadline

Response example:
```json
{
  "count": 1,
  "results": [{
    "id": 1,
    "reference_number": "RJPC-2024-12345",
    "title": "Project Example",
    "status": "in_progress",
    "start_date": "2024-01-01",
    "deadline": "2024-12-31",
    "location": "Paris",
    "created_at": "2024-01-01T00:00:00Z",
    "owner_details": {
      "id": 1,
      "username": "john.doe",
      "email": "john.doe@example.com"
    },
    "version_count": 5,
    "document_count": 3
  }]
}
```

#### Create Project
```http
POST /api/projects/
```
Request body:
```json
{
  "title": "New Project",
  "description": "Project description",
  "objectives": "Project objectives",
  "deadline": "2024-12-31",
  "start_date": "2024-01-01",
  "location": "Paris"
}
```

#### Get Project Details
```http
GET /api/projects/{id}/
```

#### Update Project
```http
PUT /api/projects/{id}/
PATCH /api/projects/{id}/
```

#### Delete Project
```http
DELETE /api/projects/{id}/
```

### Project Members

#### Add Member
```http
POST /api/projects/{id}/add_member/
```
Request body:
```json
{
  "user": "user@example.com",
  "role": "collaborator"
}
```

#### Remove Member
```http
DELETE /api/projects/{id}/remove_member/?user_id=1
```

### Project Versions

#### List Versions
```http
GET /api/projects/{id}/versions/
```
Lists all changes made to the project with their timestamps and details.

#### Restore Version
```http
POST /api/projects/{id}/restore_version/
```
Request body:
```json
{
  "version": 1
}
```

### Documents

#### List Project Documents
```http
GET /api/projects/{project_id}/documents/
```

#### Upload Document
```http
POST /api/projects/{project_id}/upload_documents/
```
Multipart form data:
- documents: File(s)
- title: String (optional)
- description: String (optional)
- document_type: String (pdf|image|video|other)

#### Update Document
```http
PUT /api/projects/{project_id}/documents/{id}/
```

#### Delete Document
```http
DELETE /api/projects/{project_id}/documents/{id}/
```

## Tasks Endpoints

### List Project Tasks
```http
GET /api/projects/{project_id}/tasks/
```
- Supports filtering by: status, assigned_to
- Supports ordering by: due_date, created_at

### Create Task
```http
POST /api/projects/{project_id}/tasks/
```
Request body:
```json
{
  "title": "Task Title",
  "description": "Task description",
  "assigned_to": "username",
  "due_date": "2024-12-31",
  "status": "open"
}
```

### Update Task
```http
PUT /api/projects/{project_id}/tasks/{id}/
PATCH /api/projects/{project_id}/tasks/{id}/
```

### Delete Task
```http
DELETE /api/projects/{project_id}/tasks/{id}/
```

## Forums and Discussions

### Forums

#### List Forums
```http
GET /api/forums/
```
- Supports filtering by: category, status
- Supports search on: title, description, category

#### Create Forum
```http
POST /api/forums/
```
Request body:
```json
{
  "title": "Forum Title",
  "description": "Forum description",
  "category": "General"
}
```

#### Get Forum Statistics
```http
GET /api/forums/{id}/statistics/
```

#### Change Forum Status
```http
POST /api/forums/{id}/change_status/
```
Request body:
```json
{
  "status": "archived"
}
```

### Discussion Groups

#### List Groups
```http
GET /api/forums/{forum_id}/groups/
```
- Supports filtering by: status, visibility
- Supports search on: theme

#### Create Group
```http
POST /api/forums/{forum_id}/groups/
```
Request body:
```json
{
  "theme": "Group Theme",
  "visibility": "public"
}
```

#### Join Group
```http
POST /api/forums/{forum_id}/groups/{id}/join/
```

#### Leave Group
```http
POST /api/forums/{forum_id}/groups/{id}/leave/
```

#### List Group Members
```http
GET /api/forums/{forum_id}/groups/{id}/members/
```

### Discussions

#### List Discussions
```http
GET /api/forums/{forum_id}/groups/{group_id}/discussions/
```
- Supports ordering by: created_at

#### Create Discussion
```http
POST /api/forums/{forum_id}/groups/{group_id}/discussions/
```
Request body:
```json
{
  "message": "Discussion message",
  "receiver": null
}
```

#### Reply to Discussion
```http
POST /api/forums/{forum_id}/groups/{group_id}/discussions/{id}/reply/
```
Request body:
```json
{
  "message": "Reply message"
}
```

#### Mark Discussion as Read
```http
POST /api/forums/{forum_id}/groups/{group_id}/discussions/{id}/mark_as_read/
```

#### Get Unread Discussions
```http
GET /api/forums/{forum_id}/groups/{group_id}/discussions/unread/
```

#### Get Discussion Thread
```http
GET /api/forums/{forum_id}/groups/{group_id}/discussions/{id}/thread/
```

## Error Responses
The API returns standard HTTP status codes:
- 200: Success
- 201: Created
- 204: No Content
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error

Error response format:
```json
{
  "error": "Error message description"
}
```

## Permissions
- `IsAuthenticated`: Required for all endpoints
- `IsProjectOwner`: Required for adding/removing project members
- `IsProjectMember`: Required for accessing project resources
- `IsForumAdmin`: Required for forum administration
- `IsGroupMember`: Required for accessing private group discussions
- `CanManageDiscussion`: Required for modifying discussions