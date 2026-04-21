def cart_context(request):
    cart_item_count = 0
    if request.user.is_authenticated:
        cart = getattr(request.user, 'shopping_cart', None)
        if cart:
            cart_item_count = cart.get_total_items()
    return {'cart_item_count': cart_item_count}
