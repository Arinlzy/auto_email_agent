# 多Embedding模型使用指南

## 概述

现在系统支持多种embedding模型，可以根据需要选择不同的提供商和模型来创建向量索引。

## 支持的Embedding提供商

### 1. 智谱AI (ZhipuAI) - 默认
- `embedding-3` (默认) - 1024维
- `embedding-2` - 1024维

### 2. OpenAI
- `text-embedding-3-small` (默认) - 1536维
- `text-embedding-3-large` - 3072维  
- `text-embedding-ada-002` - 1536维

### 3. OpenRouter (代理服务)
- `text-embedding-3-small` (默认, 通过OpenAI) - 1536维
- `text-embedding-3-large` (通过OpenAI) - 3072维
- `text-embedding-ada-002` (通过OpenAI) - 1536维

**注意**: OpenRouter是一个代理服务，根据请求的模型将请求路由到相应的后端服务（如OpenAI、Anthropic等）。

## 创建索引

### 基本用法

```bash
# 使用默认设置（智谱AI embedding-3）
python create_index.py

# 指定提供商
python create_index.py --provider openai
python create_index.py --provider zhipuai

# 指定具体模型
python create_index.py --provider openai --model text-embedding-3-large
python create_index.py --provider zhipuai --model embedding-3
```

### 高级用法

```bash
# 自定义文档分块参数
python create_index.py --provider openai --chunk-size 500 --chunk-overlap 100

# 使用自定义数据文件
python create_index.py --data ./my_data/documents.txt --provider openai

# 跳过测试查询
python create_index.py --provider openai --no-test

# 查看所有可用的提供商和模型
python create_index.py --list-providers
```

## 数据库路径

不同的embedding模型会创建独立的数据库：

```
db_zhipuai_embedding_3/     # 智谱AI embedding-3
db_openai_text_embedding_3_small/   # OpenAI small model
db_openai_text_embedding_3_large/   # OpenAI large model  
```

## 程序中使用

### 配置RAG服务使用特定embedding

```python
from src.models.base_agent import ModelProvider
from src.services.service_manager import ServiceManager

# 创建服务管理器
service_manager = ServiceManager()

# 配置使用OpenAI embedding
service_manager.configure_rag(
    embedding_provider=ModelProvider.OPENAI,
    embedding_model="text-embedding-3-large"
)

# 获取RAG服务
rag_service = service_manager.get_rag_service()

# 处理邮件获取上下文
context = rag_service.process_email_for_context(email_body)
```

### 运行时切换embedding模型

```python
# 切换到不同的embedding模型
rag_service.switch_embedding_model(
    ModelProvider.ZHIPUAI, 
    "embedding-3"
)

# 服务会自动重新初始化并使用对应的数据库
```

## 环境变量配置

确保在`.env`文件中配置相应的API密钥：

```env
# 智谱AI
ZHIPUAI_API_KEY=your_zhipuai_key

# OpenAI  
OPENAI_API_KEY=your_openai_key

# OpenRouter
OPENROUTER_API_KEY=your_openrouter_key
```

## 最佳实践

### 1. 选择合适的embedding模型

- **智谱AI embedding-3**: 中文友好，成本较低
- **OpenAI text-embedding-3-small**: 平衡性能和成本
- **OpenAI text-embedding-3-large**: 最佳精度，成本较高

### 2. 为不同语言使用不同模型

```python
# 中文内容使用智谱AI
service_manager.configure_rag(ModelProvider.ZHIPUAI, "embedding-3")

# 英文内容使用OpenAI  
service_manager.configure_rag(ModelProvider.OPENAI, "text-embedding-3-small")
```

### 3. 根据性能需求选择

- **快速检索**: 使用小模型 (embedding-3, text-embedding-3-small)
- **高精度检索**: 使用大模型 (text-embedding-3-large)

## 故障排除

### 1. 数据库不存在错误
确保先用对应的embedding模型创建索引：
```bash
python create_index.py --provider openai --model text-embedding-3-small
```

### 2. API密钥错误
检查`.env`文件中是否配置了正确的API密钥。

### 3. 模型不支持
使用 `--list-providers` 查看支持的模型列表。

## 示例workflow

```bash
# 1. 创建不同embedding的索引
python create_index.py --provider zhipuai --model embedding-3
python create_index.py --provider openai --model text-embedding-3-small

# 2. 在程序中切换使用
python -c "
from src.services.service_manager import ServiceManager
from src.models.base_agent import ModelProvider

sm = ServiceManager()

# 测试智谱AI embedding
sm.configure_rag(ModelProvider.ZHIPUAI, 'embedding-3')
print('ZhipuAI embedding configured')

# 切换到OpenAI embedding  
sm.configure_rag(ModelProvider.OPENAI, 'text-embedding-3-small')
print('OpenAI embedding configured')
"
```