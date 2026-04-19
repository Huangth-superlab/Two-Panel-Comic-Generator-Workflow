from langgraph.graph import StateGraph, END
from graphs.state import (
    GlobalState,
    GraphInput,
    GraphOutput
)
from graphs.nodes.scene_analysis_node import scene_analysis_node
from graphs.nodes.prompt_assemble_node import prompt_assemble_node
from graphs.nodes.image_gen_node import image_gen_node
from graphs.nodes.add_text_node import add_text_node

# 创建状态图，指定工作流的入参和出参
builder = StateGraph(GlobalState, input_schema=GraphInput, output_schema=GraphOutput)

# 添加节点
# 场景分析节点（合并关键因素生成和场景描述，分析情绪并生成场景描述）
builder.add_node("scene_analysis", scene_analysis_node, metadata={"type": "agent", "llm_cfg": "config/scene_analysis_llm_cfg.json"})

# 提示词组装节点（Python逻辑，不使用LLM）
builder.add_node("prompt_assemble", prompt_assemble_node)

# 图片生成节点
builder.add_node("image_gen", image_gen_node)

# 添加文字节点（使用脚本添加文字）
builder.add_node("add_text", add_text_node)

# 设置入口点
builder.set_entry_point("scene_analysis")

# 添加边
# 场景分析完成后，执行提示词组装
builder.add_edge("scene_analysis", "prompt_assemble")

# 提示词组装完成后，执行图片生成
builder.add_edge("prompt_assemble", "image_gen")

# 图片生成完成后，执行添加文字
builder.add_edge("image_gen", "add_text")

# 添加文字完成后，结束
builder.add_edge("add_text", END)

# 编译图
main_graph = builder.compile()
