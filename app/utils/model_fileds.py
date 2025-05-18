from app.models.product_image import ProductImage


def get_model_fields(model):
    return [column.name for column in model.__table__.columns if column.name != "supplier_id"]


def build_image_model_prompt():
    image_models = {
        "PRODUCT IMAGE MODEL": ProductImage,
    }

    prompt_sections = []
    for model_name, model_class in image_models.items():
        fields = get_model_fields(model_class)
        formatted_fields = "\n- " + "\n- ".join(fields)
        prompt_sections.append(f"### {model_name}{formatted_fields}")

    return "\n\n".join(prompt_sections)
