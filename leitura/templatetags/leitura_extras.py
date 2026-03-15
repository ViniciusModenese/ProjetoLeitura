from django import template

register = template.Library()


@register.filter
def star_classes(nota, pos):
    """
    Retorna as classes CSS + ícone Bootstrap Icons para uma estrela na posição `pos`.
    - nota >= pos       → estrela cheia  (bi-star-fill  star-filled)
    - nota >= pos - 0.5 → meia estrela  (bi-star-half  star-filled)
    - caso contrário    → estrela vazia  (bi-star       star-empty)
    """
    try:
        nota = float(nota or 0)
        pos = int(pos)
    except (TypeError, ValueError):
        return "bi-star star-empty"

    if nota >= pos:
        return "bi-star-fill star-filled"
    elif nota >= pos - 0.5:
        return "bi-star-half star-filled"
    else:
        return "bi-star star-empty"
