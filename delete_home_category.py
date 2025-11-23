from sqlmodel import Session, select
from cj36.dependencies import engine
from cj36.models import Category

def delete_home_category():
    with Session(engine) as session:
        statement = select(Category).where(Category.name == "প্রচ্ছদ")
        results = session.exec(statement).all()
        for category in results:
            print(f"Deleting category: {category.name}")
            session.delete(category)
        session.commit()
        print("Finished deleting 'Home' category.")

if __name__ == "__main__":
    delete_home_category()
