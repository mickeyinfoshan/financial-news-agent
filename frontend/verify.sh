#!/bin/bash

echo "🔍 Financial News Agent - 前端验证脚本"
echo "========================================"
echo ""

# 检查前端
echo "1️⃣ 检查前端服务..."
if curl -s http://localhost:5173 > /dev/null; then
    echo "   ✅ 前端运行正常 (http://localhost:5173)"
else
    echo "   ❌ 前端未运行"
    echo "   💡 启动命令: cd frontend && npm run dev"
    exit 1
fi

echo ""

# 检查后端
echo "2️⃣ 检查后端 API..."
if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    echo "   ✅ 后端 API 运行正常 (http://localhost:8000)"

    # 获取健康检查详情
    HEALTH=$(curl -s http://localhost:8000/api/v1/health)
    echo "   📊 健康状态: $HEALTH"
else
    echo "   ❌ 后端 API 未运行"
    echo "   💡 启动命令: uv run python -m financial_news_agent.api_server"
    echo "   ⚠️  前端可以运行，但无法提交查询"
fi

echo ""

# 检查 CORS 配置
echo "3️⃣ 检查 CORS 配置..."
if grep -q "localhost:5173" ../.env 2>/dev/null; then
    echo "   ✅ CORS 配置包含 localhost:5173"
else
    echo "   ⚠️  .env 中未找到 localhost:5173"
    echo "   💡 请确保 .env 包含: API_CORS_ORIGINS=http://localhost:3000,http://localhost:5173"
fi

echo ""

# 测试会话创建
echo "4️⃣ 测试 API 连接..."
if curl -s http://localhost:8000/api/v1/health > /dev/null; then
    RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/session/create \
        -H "Content-Type: application/json" \
        -d '{"query": null}')

    if echo "$RESPONSE" | grep -q "session_id"; then
        echo "   ✅ 会话创建成功"
        SESSION_ID=$(echo "$RESPONSE" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)
        echo "   📝 会话 ID: $SESSION_ID"
    else
        echo "   ❌ 会话创建失败"
        echo "   📄 响应: $RESPONSE"
    fi
else
    echo "   ⏭️  跳过（后端未运行）"
fi

echo ""
echo "========================================"
echo "✨ 验证完成！"
echo ""
echo "📱 访问前端: http://localhost:5173"
echo "📚 API 文档: http://localhost:8000/docs"
echo "📋 测试清单: frontend/TESTING_CHECKLIST.md"
echo ""
