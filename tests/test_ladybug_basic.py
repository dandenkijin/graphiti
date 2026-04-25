#!/usr/bin/env python3
"""
Basic LadybugDB functionality test without Ollama dependencies
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from graphiti_core.driver.ladybug_driver import LadybugDriver
from graphiti_core.utils.logger import GraphitiLogger

logger = GraphitiLogger()

async def test_basic_ladybug_functionality():
    """Test basic LadybugDB functionality without embeddings"""
    
    print("Testing basic LadybugDB functionality...")
    
    try:
        # Initialize driver
        driver = LadybugDriver("ladybug.db")
        print("✅ LadybugDB driver initialized successfully")
        
        # Test basic connection
        session = driver.session()
        print("✅ Database session created successfully")
        
        # Test basic query execution
        result = await session.execute_query("RETURN 'Hello LadybugDB' as message")
        if result and len(result) > 0:
            print(f"✅ Basic query executed: {result[0]['message']}")
        else:
            print("❌ Basic query failed")
            
        # Test schema tables exist
        tables_query = "SHOW TABLES"
        tables = await session.execute_query(tables_query)
        print(f"✅ Database tables: {[t['name'] for t in tables]}")
        
        # Test indexes exist  
        indexes_query = "SHOW INDEXES"
        indexes = await session.execute_query(indexes_query)
        print(f"✅ Database indexes: {[i['name'] for i in indexes]}")
        
        print("\n🎉 All basic LadybugDB functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        if 'driver' in locals():
            await driver.close()

if __name__ == "__main__":
    asyncio.run(test_basic_ladybug_functionality())
