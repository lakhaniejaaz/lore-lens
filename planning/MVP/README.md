# Planning

This is planning for MVP features of Lore Lens. 
Included is 
1) Figma Mocks
2) DB Diagrams + Explanations
3) Endpoints 

## Figma Mocks

[Figma Mocks](https://www.figma.com/design/oKXStg091VJ82UZaNsx9Lb/Lore-Lens-Mocks?node-id=0-1&p=f)

## DB 

![DB Diagram](./LoreLens_MVP_DB_Diagram.png)

## Endpoints

### /auth
- POST /register -> Creates a new user
- POST /login -> User Login
- GET /me -> user about page

### /works
- POST / -> creates a new work
- GET / -> lists all works
- GET /{work_id} -> lists a single work
- PUT /{work_id} -> edits a work

### /entities
- POST / -> creates a new entity
- GET / -> lists all entities
- GET /{entity_id} -> lists a single entity
- PUT /{entity_id} -> edits an entity

--- 

- POST /works/{work_id}/entities/{entity_id} -> links a work to an entity
- GET /works/{work_id}/entities -> lists a works entities
- GET /entities/{entity_id}/works -> lists an entities works
- DELETE /works/{work_id}/entities/{entity_id} -> deletes a work entity relationship