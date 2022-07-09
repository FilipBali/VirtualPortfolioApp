def create_ajax_message(request, messages):
    django_messages = []
    for message in messages.get_messages(request):
        django_messages.append({
            "level": message.level_tag,
            "message": message.message,
            "extra_tags": message.tags,
        })

    return django_messages