import asyncio
from agents.social_arena_agent import get_social_arena_agent

async def main():
    print("🚀 正在启动 Zero Realm Social Agent...")

    try:
        agent = get_social_arena_agent()
        
        result = await agent.run({
            "mode": "test",
            "challenge": "monitor",
            "session_context": {
                "objectives": ["gather_intelligence", "build_reputation"],
                "message": "你好，请介绍一下你的主要功能"
            }
        })
        
        print("\n✅ Agent 运行结果：")
        print(result)
        
    except Exception as e:
        print(f"\n❌ 运行出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())