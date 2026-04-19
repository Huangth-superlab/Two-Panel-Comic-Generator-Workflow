import os
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from coze_coding_dev_sdk.s3 import S3SyncStorage
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from graphs.state import AddTextInput, AddTextOutput

def add_text_node(state: AddTextInput, config: RunnableConfig, runtime: Runtime[Context]) -> AddTextOutput:
    """
    title: 添加文字
    desc: 使用脚本给图片添加上下句文字，并上传到对象存储
    integrations: 对象存储
    """
    ctx = runtime.context
    
    # 初始化对象存储客户端
    storage = S3SyncStorage(
        endpoint_url=os.getenv("COZE_BUCKET_ENDPOINT_URL"),
        access_key="",
        secret_key="",
        bucket_name=os.getenv("COZE_BUCKET_NAME"),
        region="cn-beijing",
    )
    
    # 下载图片
    response = requests.get(state.generated_image_url)
    image_bytes = response.content
    
    # 使用BytesIO打开图片
    image = Image.open(BytesIO(image_bytes))
    
    # 创建绘图对象
    draw = ImageDraw.Draw(image)
    
    # 获取图片尺寸
    width, height = image.size
    
    # 计算两格的高度（双格垂直漫画）
    panel_height = height // 2
    
    # 文字样式设置
    font_color = (0, 0, 0)  # 黑色
    stroke_color = (255, 255, 255)  # 白色边框
    stroke_width = 3  # 边框宽度
    font_size = int(width * 0.05)  # 字体大小为图片宽度的5%
    
    # 定义中文字体候选路径（按优先级排序）
    chinese_font_paths = [
        # Linux系统常见中文字体
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        # macOS中文字体
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        # Windows中文字体
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    
    # 尝试加载中文字体
    font = None
    for font_path in chinese_font_paths:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except:
            continue
    
    # 如果所有中文字体都加载失败，使用默认字体（会显示为方框）
    if font is None:
        try:
            # 最后尝试英文字体
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()
    
    # 上格文字位置（上格顶部中间）
    upper_text_y = int(panel_height * 0.15)
    
    # 下格文字位置（下格顶部中间）
    lower_text_y = int(panel_height * 1.10)
    
    # 定义绘制带白色边框的文字的函数
    def draw_text_with_stroke(draw, position, text, font, text_color, stroke_color, stroke_width):
        """
        绘制带白色边框的文字
        通过在中心文字周围多次绘制偏移的白色文字来实现描边效果
        """
        x, y = position
        # 绘制白色边框（在8个方向上偏移）
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx != 0 or dy != 0:  # 跳过中心位置
                    draw.text((x + dx, y + dy), text, fill=stroke_color, font=font)
        # 最后绘制中心的黑色文字
        draw.text((x, y), text, fill=text_color, font=font)
    
    # 添加上句文字
    upper_bbox = draw.textbbox((0, 0), state.upper_sentence, font=font)
    upper_text_width = upper_bbox[2] - upper_bbox[0]
    upper_text_x = (width - upper_text_width) // 2
    
    # 绘制上句文字（带白色边框）
    draw_text_with_stroke(
        draw=draw,
        position=(upper_text_x, upper_text_y),
        text=state.upper_sentence,
        font=font,
        text_color=font_color,
        stroke_color=stroke_color,
        stroke_width=stroke_width
    )
    
    # 添加下句文字
    lower_bbox = draw.textbbox((0, 0), state.lower_sentence, font=font)
    lower_text_width = lower_bbox[2] - lower_bbox[0]
    lower_text_x = (width - lower_text_width) // 2
    
    # 绘制下句文字（带白色边框）
    draw_text_with_stroke(
        draw=draw,
        position=(lower_text_x, lower_text_y),
        text=state.lower_sentence,
        font=font,
        text_color=font_color,
        stroke_color=stroke_color,
        stroke_width=stroke_width
    )
    
    # 将图片保存到BytesIO
    output_buffer = BytesIO()
    image.save(output_buffer, format="PNG")
    image_bytes_with_text = output_buffer.getvalue()
    
    # 上传到对象存储
    file_name = f"comic_with_text_{state.upper_sentence[:10]}.png"
    file_key = storage.upload_file(
        file_content=image_bytes_with_text,
        file_name=file_name,
        content_type="image/png"
    )
    
    # 生成签名URL
    comic_url = storage.generate_presigned_url(
        key=file_key,
        expire_time=86400  # 24小时有效期
    )
    
    return AddTextOutput(comic_with_text_url=comic_url)
