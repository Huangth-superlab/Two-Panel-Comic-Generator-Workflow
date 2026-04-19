from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from utils.file.file import File

class GlobalState(BaseModel):
    """全局状态定义"""
    # 输入参数
    upper_sentence: str = Field(default="", description="上句文案内容")
    lower_sentence: str = Field(default="", description="下句文案内容")
    explanation: Optional[str] = Field(default=None, description="解释说明（可选，用于补充上下文信息）")
    
    # 中间状态
    emotion_type: str = Field(default="", description="情绪类型（反讽/反差/惊讶/摆烂/治愈/励志/搞笑/温馨/荒诞/治愈系无厘头/怀旧/离别/困惑/顿悟）")
    emotion_analysis: str = Field(default="", description="情绪分析说明")
    upper_scene: str = Field(default="", description="上格场景描述")
    lower_scene: str = Field(default="", description="下格场景描述")
    relationship: str = Field(default="", description="两格关联关系")
    final_prompt: str = Field(default="", description="最终图片生成提示词")
    generated_image_url: str = Field(default="", description="生成的漫画图片URL（无文字）")
    
    # 输出结果
    comic_with_text_url: str = Field(default="", description="添加文字后的漫画图片URL")

class GraphInput(BaseModel):
    """工作流输入"""
    upper_sentence: str = Field(..., description="上句文案内容")
    lower_sentence: str = Field(..., description="下句文案内容")
    explanation: Optional[str] = Field(default=None, description="解释说明（可选，用于补充上下文信息）")

class GraphOutput(BaseModel):
    """工作流输出"""
    comic_with_text_url: str = Field(..., description="添加文字后的漫画图片URL")

# ============== 节点出入参定义 ==============

class SceneAnalysisInput(BaseModel):
    """场景分析节点输入（合并关键因素生成和场景描述）"""
    upper_sentence: str = Field(..., description="上句文案内容")
    lower_sentence: str = Field(..., description="下句文案内容")
    explanation: Optional[str] = Field(default=None, description="解释说明（可选，用于补充上下文信息）")

class SceneAnalysisOutput(BaseModel):
    """场景分析节点输出"""
    emotion_type: str = Field(..., description="情绪类型（反讽/反差/惊讶/摆烂/治愈/励志/搞笑/温馨/荒诞/治愈系无厘头/怀旧/离别/困惑/顿悟）")
    emotion_analysis: str = Field(..., description="情绪分析说明")
    upper_scene: str = Field(..., description="上格场景描述")
    lower_scene: str = Field(..., description="下格场景描述")
    relationship: str = Field(..., description="两格关联关系")

class PromptAssembleInput(BaseModel):
    """提示词组装节点输入"""
    upper_sentence: str = Field(..., description="上句文案内容")
    lower_sentence: str = Field(..., description="下句文案内容")
    upper_scene: str = Field(..., description="上格场景描述")
    lower_scene: str = Field(..., description="下格场景描述")
    relationship: str = Field(..., description="两格关联关系")
    emotion_type: str = Field(..., description="情绪类型")

class PromptAssembleOutput(BaseModel):
    """提示词组装节点输出"""
    final_prompt: str = Field(..., description="最终图片生成提示词")

class ImageGenInput(BaseModel):
    """图片生成节点输入"""
    final_prompt: str = Field(..., description="最终图片生成提示词")

class ImageGenOutput(BaseModel):
    """图片生成节点输出"""
    generated_image_url: str = Field(..., description="生成的漫画图片URL")

class AddTextInput(BaseModel):
    """添加文字节点输入"""
    generated_image_url: str = Field(..., description="生成的漫画图片URL（无文字）")
    upper_sentence: str = Field(..., description="上句文案内容")
    lower_sentence: str = Field(..., description="下句文案内容")

class AddTextOutput(BaseModel):
    """添加文字节点输出"""
    comic_with_text_url: str = Field(..., description="添加文字后的漫画图片URL")
