import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from cj36.main import app
from cj36.dependencies import get_db
from cj36.core.config import settings
from cj36.models import User, UserCreate, Role, Post, PostCreate, PostStatus, Category, CategoryCreate
from cj36.core.security import get_password_hash

engine = create_engine(settings.db_url)

@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def create_user_in_db(session: Session, username, password, role, post_review_before_publish):
    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        hashed_password=hashed_password,
        role=role,
        post_review_before_publish=post_review_before_publish,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture(name="admin_user")
def admin_user_fixture(session: Session):
    return create_user_in_db(session, "adminuser", "pass", Role.ADMIN, False)

@pytest.fixture(name="admin_token")
def admin_token_fixture(client: TestClient, admin_user: User):
    response = client.post(
        "/api/v1/token",
        data={"username": admin_user.username, "password": "pass"},
    )
    return response.json()["access_token"]

@pytest.fixture(name="maintainer_user")
def maintainer_user_fixture(session: Session):
    return create_user_in_db(session, "maintaineruser", "pass", Role.MAINTAINER, False)

@pytest.fixture(name="maintainer_token")
def maintainer_token_fixture(client: TestClient, maintainer_user: User):
    response = client.post(
        "/api/v1/token",
        data={"username": maintainer_user.username, "password": "pass"},
    )
    return response.json()["access_token"]

@pytest.fixture(name="writer_user")
def writer_user_fixture(session: Session):
    return create_user_in_db(session, "writeruser", "pass", Role.WRITER, True)

@pytest.fixture(name="writer_token")
def writer_token_fixture(client: TestClient, writer_user: User):
    response = client.post(
        "/api/v1/token",
        data={"username": writer_user.username, "password": "pass"},
    )
    return response.json()["access_token"]

def create_user_helper(client: TestClient, username, password, role, post_review_before_publish, headers=None):
    user_data = {
        "username": username,
        "password": password,
        "role": role.value,
        "post_review_before_publish": post_review_before_publish,
    }
    response = client.post("/api/v1/users/", json=user_data, headers=headers)
    return response

def create_category_helper(client: TestClient, name, bn_name=None, parent_id=None, headers=None):
    category_data = {"name": name, "bn_name": bn_name, "parent_id": parent_id}
    response = client.post("/api/v1/categories/", json=category_data, headers=headers)
    return response

def create_post_helper(client: TestClient, title, description, topic_ids, category_id, headers=None):
    post_data = {
        "title": title,
        "description": description,
        "topic_ids": topic_ids,
        "category_id": category_id,
    }
    response = client.post("/api/v1/posts/", json=post_data, headers=headers)
    return response

def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "cj36 API is running!"}

# User Endpoint Tests
def test_create_user_by_admin(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = create_user_helper(client, "newwriter", "newkey", Role.WRITER, True, headers)
    assert response.status_code == 200
    assert response.json()["username"] == "newwriter"
    assert response.json()["role"] == Role.WRITER.value
    assert response.json()["post_review_before_publish"] is True

def test_create_user_by_non_admin(client: TestClient, writer_token: str):
    headers = {"Authorization": f"Bearer {writer_token}"}
    response = create_user_helper(client, "anotherwriter", "anotherkey", Role.WRITER, False, headers)
    assert response.status_code == 403 # Forbidden

def test_read_users_by_admin(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 200
    users = response.json()
    assert any(user["username"] == "adminuser" for user in users)
    assert any(user["username"] == "writeruser" for user in users)

def test_read_users_by_maintainer(client: TestClient, maintainer_token: str):
    headers = {"Authorization": f"Bearer {maintainer_token}"}
    response = client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 200
    users = response.json()
    assert any(user["username"] == "adminuser" for user in users)
    assert any(user["username"] == "writeruser" for user in users)

def test_read_users_by_writer(client: TestClient, writer_token: str):
    headers = {"Authorization": f"Bearer {writer_token}"}
    response = client.get("/api/v1/users/", headers=headers)
    assert response.status_code == 403 # Forbidden

def test_read_single_user_by_admin(client: TestClient, admin_token: str, writer_user: User):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get(f"/api/v1/users/{writer_user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == writer_user.username

def test_read_single_user_by_writer(client: TestClient, writer_token: str, maintainer_user: User):
    headers = {"Authorization": f"Bearer {writer_token}"}
    response = client.get(f"/api/v1/users/{maintainer_user.id}", headers=headers)
    assert response.status_code == 403 # Forbidden

def test_update_user_by_admin(client: TestClient, admin_token: str, writer_user: User):
    headers = {"Authorization": f"Bearer {admin_token}"}
    update_data = {"post_review_before_publish": False}
    response = client.patch(f"/api/v1/users/{writer_user.id}", json=update_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["post_review_before_publish"] is False

def test_update_user_by_non_admin(client: TestClient, writer_token: str, maintainer_user: User):
    headers = {"Authorization": f"Bearer {writer_token}"}
    update_data = {"post_review_before_publish": True}
    response = client.patch(f"/api/v1/users/{maintainer_user.id}", json=update_data, headers=headers)
    assert response.status_code == 403 # Forbidden

def test_delete_user_by_admin(client: TestClient, admin_token: str, writer_user: User):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.delete(f"/api/v1/users/{writer_user.id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == writer_user.username
    
    # Verify user is deleted
    response = client.get(f"/api/v1/users/{writer_user.id}", headers=headers)
    assert response.status_code == 404

def test_delete_user_by_non_admin(client: TestClient, writer_token: str, maintainer_user: User):
    headers = {"Authorization": f"Bearer {writer_token}"}
    response = client.delete(f"/api/v1/users/{maintainer_user.id}", headers=headers)
    assert response.status_code == 403 # Forbidden

def test_login_for_access_token(client: TestClient, admin_user: User):
    response = client.post(
        "/api/v1/token",
        data={"username": admin_user.username, "password": "adminkey"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


# Category Endpoint Tests
def test_create_category_by_maintainer(client: TestClient, maintainer_token: str):
    headers = {"Authorization": f"Bearer {maintainer_token}"}
    response = create_category_helper(client, "Test Category", "টিভি", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Category"

def test_create_category_by_writer(client: TestClient, writer_token: str):
    headers = {"Authorization": f"Bearer {writer_token}"}
    response = create_category_helper(client, "Forbidden Category", headers=headers)
    assert response.status_code == 403 # Forbidden

def test_read_categories_public(client: TestClient):
    response = client.get("/api/v1/categories/")
    assert response.status_code == 200
    # Should be able to read categories created by maintainer/admin

def test_read_categories_by_maintainer(client: TestClient, maintainer_token: str):
    headers = {"Authorization": f"Bearer {maintainer_token}"}
    response = client.get("/api/v1/categories/", headers=headers)
    assert response.status_code == 200

def test_read_single_category_by_public(client: TestClient, maintainer_token: str):
    headers = {"Authorization": f"Bearer {maintainer_token}"}
    create_category_helper(client, "Single Read Category", headers=headers)
    category_id = client.get("/api/v1/categories/", headers=headers).json()[0]["id"]
    response = client.get(f"/api/v1/categories/{category_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Single Read Category"

def test_update_category_by_admin(client: TestClient, admin_token: str, maintainer_token: str):
    headers_maintainer = {"Authorization": f"Bearer {maintainer_token}"}
    create_category_helper(client, "Category to Update", headers=headers_maintainer)
    category_id = client.get("/api/v1/categories/", headers=headers_maintainer).json()[0]["id"]

    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    update_data = {"name": "Updated Category Name"}
    response = client.put(f"/api/v1/categories/{category_id}", json=update_data, headers=headers_admin)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Category Name"

def test_update_category_by_maintainer(client: TestClient, maintainer_token: str):
    headers = {"Authorization": f"Bearer {maintainer_token}"}
    create_category_helper(client, "Another Category", headers=headers)
    category_id = client.get("/api/v1/categories/", headers=headers).json()[0]["id"]
    
    update_data = {"name": "Attempted Update"}
    response = client.put(f"/api/v1/categories/{category_id}", json=update_data, headers=headers)
    assert response.status_code == 403 # Forbidden

def test_delete_category_by_admin(client: TestClient, admin_token: str, maintainer_token: str):
    headers_maintainer = {"Authorization": f"Bearer {maintainer_token}"}
    create_category_helper(client, "Category to Delete", headers=headers_maintainer)
    category_id = client.get("/api/v1/categories/", headers=headers_maintainer).json()[0]["id"]

    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    response = client.delete(f"/api/v1/categories/{category_id}", headers=headers_admin)
    assert response.status_code == 200

def test_delete_category_by_maintainer(client: TestClient, maintainer_token: str):
    headers = {"Authorization": f"Bearer {maintainer_token}"}
    create_category_helper(client, "Category to Delete by Maintainer", headers=headers)
    category_id = client.get("/api/v1/categories/", headers=headers).json()[0]["id"]
    
    response = client.delete(f"/api/v1/categories/{category_id}", headers=headers)
    assert response.status_code == 403 # Forbidden

# Post Endpoint Tests
def test_create_post_by_writer_pending(client: TestClient, writer_token: str, maintainer_token: str):
    headers_maintainer = {"Authorization": f"Bearer {maintainer_token}"}
    response_cat = create_category_helper(client, "Tech", headers=headers_maintainer)
    category_id = response_cat.json()["id"]

    headers_writer = {"Authorization": f"Bearer {writer_token}"}
    response = create_post_helper(client, "My Pending Post", "This is a pending post.", [category_id], category_id, headers_writer)
    assert response.status_code == 200
    assert response.json()["status"] == PostStatus.PENDING.value

def test_create_post_by_writer_published(client: TestClient, admin_token: str, writer_user: User, maintainer_token: str):
    headers_maintainer = {"Authorization": f"Bearer {maintainer_token}"}
    response_cat = create_category_helper(client, "Sports", headers=headers_maintainer)
    category_id = response_cat.json()["id"]

    # Update writer_user to have post_review_before_publish = False
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    client.patch(f"/api/v1/users/{writer_user.id}", json={"post_review_before_publish": False}, headers=headers_admin)

    writer_token = client.post(
        "/api/v1/token",
        data={"username": writer_user.username, "password": "pass"},
    ).json()["access_token"]
    headers_writer = {"Authorization": f"Bearer {writer_token}"}
    response = create_post_helper(client, "My Published Post", "This is a published post.", [category_id], category_id, headers_writer)
    assert response.status_code == 200
    assert response.json()["status"] == PostStatus.PUBLISHED.value

def test_read_posts_anonymous(client: TestClient, admin_token: str, writer_user: User, maintainer_token: str):
    headers_maintainer = {"Authorization": f"Bearer {maintainer_token}"}
    response_cat = create_category_helper(client, "News", headers=headers_maintainer)
    category_id = response_cat.json()["id"]
    
    # Create a pending post
    headers_writer = {"Authorization": f"Bearer {client.post('/api/v1/token', data={'username': writer_user.username, 'password': 'writerkey'}).json()['access_token']}"}
    create_post_helper(client, "Anon Pending Post", "Pending content.", [category_id], category_id, headers_writer)
    
    # Create a published post
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    admin_category_id = create_category_helper(client, "Admin Cat", headers=headers_admin).json()["id"]
    create_post_helper(client, "Anon Published Post", "Published content.", [admin_category_id], admin_category_id, headers_admin)
    
    response = client.get("/api/v1/posts/")
    assert response.status_code == 200
    posts = response.json()
    assert len(posts) == 1
    assert posts[0]["title"] == "Anon Published Post"

def test_read_posts_writer(client: TestClient, writer_token: str, admin_token: str, writer_user: User, maintainer_token: str):
    headers_maintainer = {"Authorization": f"Bearer {maintainer_token}"}
    response_cat = create_category_helper(client, "Drafts", headers=headers_maintainer)
    category_id = response_cat.json()["id"]

    # Create a draft post by writer_user
    headers_writer = {"Authorization": f"Bearer {writer_token}"}
    create_post_helper(client, "Writer Draft Post", "Draft content.", [category_id], category_id, headers_writer)
    
    # Create another writer's published post
    other_writer = create_user_in_db(client.app.dependency_overrides[get_db](), "otherwriter", "otherpass", Role.WRITER, False)
    other_writer_token = client.post("/api/v1/token", data={"username": "otherwriter", "password": "otherpass"}).json()["access_token"]
    headers_other_writer = {"Authorization": f"Bearer {other_writer_token}"}
    create_post_helper(client, "Other Writer Published", "Other content.", [category_id], category_id, headers_other_writer)

    response = client.get("/api/v1/posts/", headers=headers_writer)
    assert response.status_code == 200
    posts = response.json()
    assert len(posts) == 2
    assert any(post["title"] == "Writer Draft Post" for post in posts)
    assert any(post["title"] == "Other Writer Published" for post in posts)

def test_read_posts_maintainer(client: TestClient, maintainer_token: str, admin_token: str, writer_user: User, session: Session):
    headers_maintainer = {"Authorization": f"Bearer {maintainer_token}"}
    response_cat = create_category_helper(client, "All Posts", headers=headers_maintainer)
    category_id = response_cat.json()["id"]

    # Writer pending post
    session.exec(select(User).where(User.username == writer_user.username)).first().post_review_before_publish = True
    session.commit()
    headers_writer = {"Authorization": f"Bearer {client.post('/api/v1/token', data={'username': writer_user.username, 'password': 'writerkey'}).json()['access_token']}"}
    create_post_helper(client, "Maintainer Pending Post", "Pending content.", [category_id], category_id, headers_writer)
    
    # Admin published post
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    admin_category_id = create_category_helper(client, "Admin Cat 2", headers=headers_admin).json()["id"]
    create_post_helper(client, "Maintainer Admin Post", "Admin content.", [admin_category_id], admin_category_id, headers_admin)

    response = client.get("/api/v1/posts/", headers=headers_maintainer)
    assert response.status_code == 200
    posts = response.json()
    assert len(posts) == 2
    assert any(post["title"] == "Maintainer Pending Post" for post in posts)
    assert any(post["title"] == "Maintainer Admin Post" for post in posts)

def test_read_single_post_anonymous(client: TestClient, admin_token: str, maintainer_token: str):
    headers_maintainer = {"Authorization": f"Bearer {maintainer_token}"}
    response_cat = create_category_helper(client, "Anon View", headers=headers_maintainer)
    category_id = response_cat.json()["id"]

    # Published post
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    published_post = create_post_helper(client, "Anon Single Published", "Content.", [category_id], category_id, headers_admin).json()

    # Pending post
    writer_user = create_user_in_db(client.app.dependency_overrides[get_db](), "anonwriter", "pass", Role.WRITER, True)
    headers_writer = {"Authorization": f"Bearer {client.post('/api/v1/token', data={'username': 'anonwriter', 'password': 'pass'}).json()['access_token']}"}
    pending_post = create_post_helper(client, "Anon Single Pending", "Content.", [category_id], category_id, headers_writer).json()

    response = client.get(f"/api/v1/posts/{published_post['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Anon Single Published"

    response = client.get(f"/api/v1/posts/{pending_post['id']}")
    assert response.status_code == 403 # Forbidden

def test_update_post_by_writer_own_post(client: TestClient, writer_token: str, maintainer_token: str, writer_user: User):
    headers_maintainer = {"Authorization": f"Bearer {maintainer_token}"}
    response_cat = create_category_helper(client, "Update Own", headers=headers_maintainer)
    category_id = response_cat.json()["id"]

    headers_writer = {"Authorization": f"Bearer {writer_token}"}
    post_data = create_post_helper(client, "Old Title", "Old Description", [category_id], category_id, headers_writer).json()
    
    update_data = {"title": "New Title", "description": "New Description"}
    response = client.patch(f"/api/v1/posts/{post_data['id']}", json=update_data, headers=headers_writer)
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["description"] == "New Description"

def test_update_post_by_writer_other_post(client: TestClient, writer_token: str, admin_token: str, maintainer_token: str):
    headers_maintainer = {"Authorization": f"Bearer {maintainer_token}"}
    response_cat = create_category_helper(client, "Update Other", headers=headers_maintainer)
    category_id = response_cat.json()["id"]
    
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    other_post = create_post_helper(client, "Other Post", "Content.", [category_id], category_id, headers_admin).json()

    headers_writer = {"Authorization": f"Bearer {writer_token}"}
    update_data = {"title": "Attempt Update"}
    response = client.patch(f"/api/v1/posts/{other_post['id']}", json=update_data, headers=headers_writer)
    assert response.status_code == 403 # Forbidden

def test_update_post_status_by_maintainer(client: TestClient, maintainer_token: str, writer_user: User, admin_token: str):
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    response_cat = create_category_helper(client, "Status Update", headers=headers_admin)
    category_id = response_cat.json()["id"]

    # Create a pending post by writer
    client.patch(f"/api/v1/users/{writer_user.id}", json={"post_review_before_publish": True}, headers=headers_admin)
    writer_token = client.post("/api/v1/token", data={"username": writer_user.username, "password": "writerkey"}).json()["access_token"]
    headers_writer = {"Authorization": f"Bearer {writer_token}"}
    pending_post = create_post_helper(client, "Pending for Approval", "Needs approval.", [category_id], category_id, headers_writer).json()

    # Maintainer approves
    headers_maintainer = {"Authorization": f"Bearer {maintainer_token}"}
    response = client.patch(f"/api/v1/posts/status/{pending_post['id']}", json=PostStatus.PUBLISHED.value, headers=headers_maintainer)
    assert response.status_code == 200
    assert response.json()["status"] == PostStatus.PUBLISHED.value

    # Maintainer rejects
    pending_post_2 = create_post_helper(client, "Pending for Rejection", "Needs rejection.", [category_id], category_id, headers_writer).json()
    response = client.patch(f"/api/v1/posts/status/{pending_post_2['id']}", json=PostStatus.REJECTED.value, headers=headers_maintainer)
    assert response.status_code == 200
    assert response.json()["status"] == PostStatus.REJECTED.value

def test_update_post_status_by_writer(client: TestClient, writer_token: str, maintainer_token: str, writer_user: User, admin_token: str):
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    response_cat = create_category_helper(client, "Writer Status", headers=headers_admin)
    category_id = response_cat.json()["id"]

    client.patch(f"/api/v1/users/{writer_user.id}", json={"post_review_before_publish": True}, headers=headers_admin)
    writer_token = client.post("/api/v1/token", data={"username": writer_user.username, "password": "writerkey"}).json()["access_token"]
    headers_writer = {"Authorization": f"Bearer {writer_token}"}
    
    pending_post = create_post_helper(client, "Writer status attempt", "Content.", [category_id], category_id, headers_writer).json()

    response = client.patch(f"/api/v1/posts/status/{pending_post['id']}", json=PostStatus.PUBLISHED.value, headers=headers_writer)
    assert response.status_code == 403 # Forbidden

def test_delete_post_by_writer_own_post(client: TestClient, writer_token: str, maintainer_token: str):
    headers_maintainer = {"Authorization": f"Bearer {maintainer_token}"}
    response_cat = create_category_helper(client, "Delete Own", headers=headers_maintainer)
    category_id = response_cat.json()["id"]

    headers_writer = {"Authorization": f"Bearer {writer_token}"}
    post_data = create_post_helper(client, "Post to Delete", "Content.", [category_id], category_id, headers_writer).json()
    
    response = client.delete(f"/api/v1/posts/{post_data['id']}", headers=headers_writer)
    assert response.status_code == 200

def test_delete_post_by_writer_other_post(client: TestClient, writer_token: str, admin_token: str, maintainer_token: str):
    headers_maintainer = {"Authorization": f"Bearer {maintainer_token}"}
    response_cat = create_category_helper(client, "Delete Other", headers=headers_maintainer)
    category_id = response_cat.json()["id"]

    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    other_post = create_post_helper(client, "Other Post to Delete", "Content.", [category_id], category_id, headers_admin).json()

    headers_writer = {"Authorization": f"Bearer {writer_token}"}
    response = client.delete(f"/api/v1/posts/{other_post['id']}", headers=headers_writer)
    assert response.status_code == 403 # Forbidden
