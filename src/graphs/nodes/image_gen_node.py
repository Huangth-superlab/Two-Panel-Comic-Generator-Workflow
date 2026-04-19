import os
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import ImageGenerationClient, S3SyncStorage
from graphs.state import ImageGenInput, ImageGenOutput

def image_gen_node(state: ImageGenInput, config: RunnableConfig, runtime: Runtime[Context]) -> ImageGenOutput:
    """
    title: 图片生成
    desc: 使用提示词和参考图生成双格治愈系漫画
    integrations: 图片生成, 对象存储
    """
    ctx = runtime.context
    
    # 初始化对象存储客户端（用于上传本地参考图）
    storage = S3SyncStorage(
        endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
        access_key="",
        secret_key="",
        bucket_name=os.getenv("COZE_BUCKET_NAME"),
        region="cn-beijing",
    )
    
    # 定义本地文件路径
    workspace_path = os.getenv("COZE_WORKSPACE_PATH")
    character_design_path = os.path.join(workspace_path, "assets/猪猪角色设计图.png")
    frame_template_path = os.path.join(workspace_path, "assets/框体模板.png")
    
    # 上传角色设计图到对象存储
    with open(character_design_path, 'rb') as f:
        character_design_content = f.read()
    character_design_key = storage.upload_file(
        file_content=character_design_content,
        file_name="character_design.png",
        content_type="image/png"
    )
    character_design_url = storage.generate_presigned_url(key=character_design_key, expire_time=86400)
    
    # 上传框体模板到对象存储
    with open(frame_template_path, 'rb') as f:
        frame_template_content = f.read()
    frame_template_key = storage.upload_file(
        file_content=frame_template_content,
        file_name="frame_template.png",
        content_type="image/png"
    )
    frame_template_url = storage.generate_presigned_url(key=frame_template_key, expire_time=86400)
    
    # 创建图片生成客户端
    client = ImageGenerationClient(ctx=ctx)
    
    # 准备参考图列表：角色设计图 + 框体模板
    reference_images = [character_design_url, frame_template_url]
    
    # 调用图片生成API
    # image 参数接受列表，多个参考图用于保持角色一致性和框体风格
    # watermark=False 禁用水印
    response = client.generate(
        prompt=state.final_prompt,
        image=reference_images,
        size="2K",
        model="doubao-seedream-5-0-260128",
        watermark=False,
        response_format="url"
    )
    
    # 检查是否成功
    if not response.success:
        error_msg = response.error_messages if response.error_messages else "Unknown error"
        raise Exception(f"Image generation failed: {error_msg}")
    
    # 获取生成的图片URL
    if not response.image_urls or len(response.image_urls) == 0:
        raise Exception("No image URLs returned from image generation")
    
    generated_image_url = response.image_urls[0]
    
    return ImageGenOutput(generated_image_url=generated_image_url)
