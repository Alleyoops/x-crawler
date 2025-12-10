#!/usr/bin/env python3
"""
LLM 配置自检与连通性测试

- 读取 .env / config.json 的 LLM 配置
- 打印已识别的 API Key / 模型 / Base URL
- 初始化 Summarizer（不发送真实业务请求）
- 发送一条最小化测试消息验证模型是否能返回响应
"""

from config_loader import ConfigLoader
from summarizer import TwitterSummarizer


def main():
    loader = ConfigLoader()

    api_key = loader.get("llm.api_key")
    model = loader.get("llm.model")
    base_url = loader.get("llm.base_url")

    print("🛠️ LLM 配置检测")
    print("-" * 40)
    if api_key:
        masked = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
        print(f"API Key: 已配置 ({masked})")
    else:
        print("API Key: 未找到 (请设置 LLM_API_KEY / DEEPSEEK_API_KEY / OPENROUTER_API_KEY 等)")

    print(f"模型: {model or '未设置'}")
    print(f"Base URL: {base_url or '未设置'}")

    print("\n⏳ 初始化 Summarizer（只检查依赖和配置，不会调用真实接口）...")
    try:
        TwitterSummarizer(api_key=api_key, model=model, base_url=base_url)
        print("✅ 初始化完成，请留意上方输出的依赖/模型/接口地址信息。")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        print("💡 请检查网络、openai 库安装，以及 Base URL 是否为可用的 OpenAI 兼容接口。")
        return

    # 发送一次最小化的问答请求，验证是否可用
    print("\n🤖 发送测试请求到大模型...")
    try:
        try:
            from openai import OpenAI
        except ImportError:
            print("⚠️ 未安装 openai 库，请先运行: pip install openai")
            return

        if not api_key:
            print("❌ 缺少 API Key，无法请求。请设置环境变量 LLM_API_KEY / DEEPSEEK_API_KEY / OPENROUTER_API_KEY 等。")
            return

        target_model = model or "deepseek-chat"
        target_base_url = base_url or "https://openrouter.ai/api/v1"

        extra_headers = None
        if "openrouter.ai" in target_base_url:
            extra_headers = {
                "HTTP-Referer": "https://github.com/anthropics/claude-code",
                "X-Title": "X-Tweet-Analysis-System",
            }

        # 使用新版 OpenAI 客户端（1.x），不再回退旧接口以避免不兼容报错
        client = OpenAI(base_url=target_base_url, api_key=api_key)

        prompt = "这是一次连通性测试。请简单回复：已收到。"
        resp = client.chat.completions.create(
            model=target_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=30,
            temperature=0,
            extra_headers=extra_headers,
        )
        content = resp.choices[0].message.content.strip() if resp and getattr(resp, "choices", None) else ""
        print(f"✅ 模型响应: {content!r}")
    except Exception as e:
        print(f"❌ 模型调用失败: {e}")
        print("💡 检查事项：")
        print("   - API Key 是否正确，是否有权限调用目标模型；")
        print("   - Base URL 是否填写正确（OpenRouter/DeepSeek/OpenAI 兼容接口）；")
        print("   - 是否需要代理 / 是否有网络访问权限。")

    print("\n下一步建议：")
    print("1) 运行 `python test_config.py` 确认整体配置。")
    print("2) 运行 `python run_crawler.py --user-summaries` 做一次真实调用验证。")


if __name__ == "__main__":
    main()
