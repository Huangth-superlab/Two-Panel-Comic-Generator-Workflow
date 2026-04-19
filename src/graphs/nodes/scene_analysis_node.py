import os
import json
from jinja2 import Template
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from langchain_core.messages import HumanMessage, SystemMessage
from coze_coding_dev_sdk import LLMClient
from graphs.state import SceneAnalysisInput, SceneAnalysisOutput

def scene_analysis_node(state: SceneAnalysisInput, config: RunnableConfig, runtime: Runtime[Context]) -> SceneAnalysisOutput:
    """
    title: 场景分析与描述生成
    desc: 分析上下句文案的情绪特征（反讽、反差、惊讶、摆烂等），直接生成双格漫画场景描述
    integrations: 大语言模型
    """
    ctx = runtime.context

    # 读取配置文件
    cfg_file = os.path.join(os.getenv("COZE_WORKSPACE_PATH"), config['metadata']['llm_cfg'])
    with open(cfg_file, 'r', encoding='utf-8') as fd:
        _cfg = json.load(fd)

    llm_config = _cfg.get("config", {})
    sp = _cfg.get("sp", "")
    up_template_str = _cfg.get("up", "")

    # 使用jinja2模板渲染用户提示词
    up_template = Template(up_template_str)
    up = up_template.render(
        upper_sentence=state.upper_sentence,
        lower_sentence=state.lower_sentence,
        explanation=state.explanation if state.explanation else None
    )

    # 调用大模型
    client = LLMClient(ctx=ctx)
    messages = [
        SystemMessage(content=sp),
        HumanMessage(content=up)
    ]

    response = client.invoke(
        messages=messages,
        model=llm_config.get("model", "doubao-seed-2-0-lite-260215"),
        temperature=llm_config.get("temperature", 0.8),
        top_p=llm_config.get("top_p", 0.8),
        max_completion_tokens=llm_config.get("max_completion_tokens", 2500)
    )

    # 提取文本内容
    content = response.content
    if isinstance(content, str):
        result_text = content.strip()
    elif isinstance(content, list):
        result_text = " ".join([item if isinstance(item, str) else str(item) for item in content])
    else:
        result_text = str(content)

    # 解析JSON结果
    try:
        # 尝试提取JSON部分
        json_start = result_text.find('{')
        json_end = result_text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = result_text[json_start:json_end]
            scene_data = json.loads(json_str)
            emotion_type = scene_data.get("emotion_type", "治愈")
            emotion_analysis = scene_data.get("emotion_analysis", "")
            upper_scene = scene_data.get("upper_scene", "一只可爱的粉色小猪在温暖的环境中")
            lower_scene = scene_data.get("lower_scene", "同样的粉色小猪在另一个场景中")
            relationship = scene_data.get("relationship", "对比")
        else:
            raise ValueError("No JSON found in response")
    except Exception as e:
        # 如果JSON解析失败，返回默认描述
        emotion_type = "治愈"
        emotion_analysis = "基于文案的温暖治愈情绪"
        upper_scene = "一只圆滚滚的粉色小猪安静地坐着，周围是柔和的粉色和淡黄色调，温暖的阳光洒在身上，表情平静温柔"
        lower_scene = "同样的粉色小猪在稍有不同的场景中，保持着治愈的氛围，表情充满期待和希望"
        relationship = "递进"

    return SceneAnalysisOutput(
        emotion_type=emotion_type,
        emotion_analysis=emotion_analysis,
        upper_scene=upper_scene,
        lower_scene=lower_scene,
        relationship=relationship
    )
