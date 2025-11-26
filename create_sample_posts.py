#!/usr/bin/env python3
"""
Script to create sample posts for testing.
Usage: uv run python create_sample_posts.py
"""
from sqlmodel import Session, select
from cj36.dependencies import engine
from cj36.models import Post, PostStatus, Category, User, AdminType
import datetime

def create_sample_posts():
    """Create sample posts for testing."""
    with Session(engine) as session:
        # Get admin user
        admin = session.exec(select(User).where(User.username == "admin")).first()
        if not admin:
            with open("creation_log.txt", "a") as f:
                f.write("❌ Admin user not found.\n")
            print("❌ Admin user not found. Please run create_admin_simple.py first.")
            return
        
        # Get categories
        categories = session.exec(select(Category)).all()
        if not categories:
            with open("creation_log.txt", "a") as f:
                f.write("❌ No categories found.\n")
            print("❌ No categories found. Please seed categories first.")
            return
        
        # Check if posts already exist
        existing_posts = session.exec(select(Post)).all()
        if existing_posts:
            with open("creation_log.txt", "a") as f:
                f.write(f"ℹ️  {len(existing_posts)} posts already exist.\n")
            print(f"ℹ️  {len(existing_posts)} posts already exist.")
            response = input("Do you want to create more sample posts? (yes/no): ").strip().lower()
            if response != "yes":
                with open("creation_log.txt", "a") as f:
                    f.write("❌ Operation cancelled.\n")
                print("❌ Operation cancelled.")
                return
        
        print("\n📝 Creating sample posts...")
        
        # Sample posts data
        sample_posts = [
            {
                "title": "Breaking: Major Technology Breakthrough Announced",
                "description": "<p>Scientists have announced a groundbreaking discovery in quantum computing that could revolutionize the tech industry. This development promises to solve complex problems that were previously impossible to tackle.</p><p>The research team, led by renowned physicist Dr. Sarah Chen, demonstrated a quantum processor capable of performing calculations 1000 times faster than current supercomputers.</p>",
                "category_id": categories[0].id if len(categories) > 0 else None,
                "status": PostStatus.PUBLISHED,
                "image": "https://picsum.photos/800/600?random=1"
            },
            {
                "title": "Local Community Comes Together for Charity Event",
                "description": "<p>Hundreds of volunteers gathered at the city center today for the annual charity drive, raising over $50,000 for local schools and hospitals.</p><p>The event featured live music, food stalls, and activities for children, creating a festive atmosphere while supporting important causes.</p>",
                "category_id": categories[1].id if len(categories) > 1 else categories[0].id,
                "status": PostStatus.PUBLISHED,
                "image": "https://picsum.photos/800/600?random=2"
            },
            {
                "title": "Sports Update: Championship Finals This Weekend",
                "description": "<p>The highly anticipated championship finals are set to take place this weekend, with teams from across the region competing for the coveted trophy.</p><p>Fans are expected to fill the stadium to capacity, creating an electric atmosphere for what promises to be an unforgettable match.</p>",
                "category_id": categories[2].id if len(categories) > 2 else categories[0].id,
                "status": PostStatus.PUBLISHED,
                "image": "https://picsum.photos/800/600?random=3"
            },
            {
                "title": "New Restaurant Opens Downtown with Unique Cuisine",
                "description": "<p>Food enthusiasts have a new destination to explore as 'Fusion Delights' opens its doors in the heart of downtown.</p><p>The restaurant offers a unique blend of traditional and modern cuisine, with dishes crafted by award-winning chef Michael Rodriguez.</p>",
                "category_id": categories[0].id if len(categories) > 0 else None,
                "status": PostStatus.PUBLISHED,
                "image": "https://picsum.photos/800/600?random=4"
            },
            {
                "title": "Weather Alert: Sunny Weekend Ahead",
                "description": "<p>Meteorologists predict perfect weather conditions for the upcoming weekend, with clear skies and temperatures in the mid-70s.</p><p>This is an ideal time for outdoor activities, picnics, and enjoying nature after weeks of unpredictable weather.</p>",
                "category_id": categories[1].id if len(categories) > 1 else categories[0].id,
                "status": PostStatus.PUBLISHED,
                "image": "https://picsum.photos/800/600?random=5"
            },
            {
                "title": "Education: New STEM Program Launches in Schools",
                "description": "<p>Local schools are introducing an innovative STEM program designed to inspire the next generation of scientists and engineers.</p><p>The program includes hands-on workshops, mentorship opportunities, and access to state-of-the-art laboratory equipment.</p>",
                "category_id": categories[2].id if len(categories) > 2 else categories[0].id,
                "status": PostStatus.PUBLISHED,
                "image": "https://picsum.photos/800/600?random=6"
            },
            {
                "title": "Health Tips: Staying Active During Winter Months",
                "description": "<p>Health experts share valuable tips for maintaining an active lifestyle during the colder months when outdoor activities become challenging.</p><p>From indoor exercises to nutrition advice, this comprehensive guide helps you stay healthy year-round.</p>",
                "category_id": categories[0].id if len(categories) > 0 else None,
                "status": PostStatus.PUBLISHED,
                "image": "https://picsum.photos/800/600?random=7"
            },
            {
                "title": "Business News: Local Startup Secures Major Investment",
                "description": "<p>A promising local startup has secured $5 million in Series A funding, marking a significant milestone in its growth journey.</p><p>The company, which specializes in sustainable packaging solutions, plans to use the funds to expand operations and hire additional staff.</p>",
                "category_id": categories[1].id if len(categories) > 1 else categories[0].id,
                "status": PostStatus.PUBLISHED,
                "image": "https://picsum.photos/800/600?random=8"
            },
            {
                "title": "Arts & Culture: Museum Unveils New Exhibition",
                "description": "<p>The city museum is proud to present its latest exhibition featuring contemporary art from emerging local artists.</p><p>The collection showcases diverse perspectives and innovative techniques, offering visitors a fresh look at modern artistic expression.</p>",
                "category_id": categories[2].id if len(categories) > 2 else categories[0].id,
                "status": PostStatus.PUBLISHED,
                "image": "https://picsum.photos/800/600?random=9"
            },
            {
                "title": "Travel: Top 10 Hidden Gems to Visit This Year",
                "description": "<p>Discover breathtaking destinations that most tourists overlook. Our travel experts have compiled a list of hidden gems perfect for adventurous travelers.</p><p>From secluded beaches to mountain retreats, these locations offer unique experiences away from crowded tourist spots.</p>",
                "category_id": categories[0].id if len(categories) > 0 else None,
                "status": PostStatus.PUBLISHED,
                "image": "https://picsum.photos/800/600?random=10"
            }
        ]
        
        created_count = 0
        for post_data in sample_posts:
            post = Post(
                **post_data,
                author_id=admin.id,
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow()
            )
            session.add(post)
            created_count += 1
            with open("creation_log.txt", "a") as f:
                f.write(f"  ✅ Created: {post.title[:50]}...\n")
            print(f"  ✅ Created: {post.title[:50]}...")
        
        session.commit()
        
        print(f"\n✅ Successfully created {created_count} sample posts!")
        print("=" * 60)
        print("You can now test the application with real data.")
        print("=" * 60)



if __name__ == "__main__":
    try:
        with open("creation_log.txt", "w") as f:
            f.write("Starting script...\n")
        create_sample_posts()
    except Exception as e:
        with open("creation_log.txt", "a") as f:
            f.write(f"❌ Error creating sample posts: {e}\n")
        print(f"❌ Error creating sample posts: {e}")
        raise

