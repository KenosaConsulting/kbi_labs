#!/usr/bin/env python3
"""Test infrastructure components"""
import asyncio
import sys

async def test_kafka():
    """Test Kafka connectivity"""
    print("Testing Kafka...")
    try:
        from kafka_infrastructure import KafkaInfrastructure
        kafka = KafkaInfrastructure()
        if kafka.initialize():
            health = kafka.health_check()
            print(f"✅ Kafka is healthy: {health['status']}")
            return True
    except Exception as e:
        print(f"❌ Kafka test failed: {e}")
        return False

async def test_database():
    """Test PostgreSQL connectivity"""
    print("\nTesting PostgreSQL...")
    try:
        from database_manager import db_manager
        await db_manager.initialize()
        health = await db_manager.health_check()
        print(f"✅ PostgreSQL is healthy: {health['status']}")
        await db_manager.close()
        return True
    except Exception as e:
        print(f"❌ PostgreSQL test failed: {e}")
        return False

async def test_redis():
    """Test Redis connectivity"""
    print("\nTesting Redis...")
    try:
        import redis
        r = redis.from_url('redis://localhost:6379')
        r.ping()
        print("✅ Redis is healthy")
        return True
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🔧 KBI Labs Infrastructure Tests")
    print("================================\n")
    
    # Run tests
    kafka_ok = await test_kafka()
    db_ok = await test_database()
    redis_ok = await test_redis()
    
    print("\n📊 Test Summary:")
    print(f"  Kafka: {'✅ Passed' if kafka_ok else '❌ Failed'}")
    print(f"  PostgreSQL: {'✅ Passed' if db_ok else '❌ Failed'}")
    print(f"  Redis: {'✅ Passed' if redis_ok else '❌ Failed'}")
    
    if all([kafka_ok, db_ok, redis_ok]):
        print("\n🎉 All tests passed! Infrastructure is ready.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the services.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
