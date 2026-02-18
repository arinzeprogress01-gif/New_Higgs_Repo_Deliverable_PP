import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.utils.security import verify_password
from app.utils.security import hash_password
from app.models import User, Cart, CartItem, Order, OrderItem, Food, Payment

router = APIRouter()

@router.post("/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already Registered"
        )

    if len(user.password) < 6: 
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 6 characters"
        )
    hashed_password = hash_password(user.password)
    otp = str(random.randint(100000, 999999))

    new_user = models.User(
        email=user.email,
        phone=user.phone,
        hashed_password=hashed_password,
        is_verified=False,
        otp=otp
    )
    db.add(new_user)
    db.commit()
    print("User OTP:", otp)
    db.refresh(new_user)

    new_cart = models.Cart(
        user_id=new_user.id,
    )
    db.add(new_cart)
    db.commit()

    return {"message": "User created successfully"}

@router.post("/login")
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):

    db_user = db.query(models.User).filter(
        models.User.email == login_data.email
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=404, 
            detail="User not found")

    if not verify_password(login_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=401, 
            detail="Incorrect password")

    return {"message": "Login successful"}


@router.post("/verify")
def verify_user(data: schemas.VerifyUser, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not Found"
        )

    if user.is_verified:
        return {"message": "User Already Verified"}
        #Proper edge case senario to prevent dual verification
    if user.otp != data.otp:
        raise HTTPException(
            status_code=400,
            detail="Invalid OTP"
        )
    
    user.is_verified = True
    user.otp = None
    db.commit()
    return {"message": "ACCOUNT VERIFICATION SUCCESSFUL"}

@router.get("/users", response_model=list[schemas.GetUser])
def get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()

    return users

@router.post("/food")
def create_food(food: schemas.FoodCreate, db: Session = Depends(get_db)):
    existing_food = db.query(models.Food).filter(models.Food.name == food.name).first()

    if existing_food:
        raise HTTPException(
        status_code=400,
        detail="Food with this name already exists"
    )

    new_food = models.Food(
        name=food.name,
        description=food.description,
        price=food.price,
        is_available=True      
    )
  
    db.add(new_food)
    db.commit()
    db.refresh(new_food)
   
    return new_food

@router.get("/foods", response_model=list[schemas.FoodResponse])
def get_foods(db: Session = Depends(get_db)):
    foods = db.query(models.Food).filter(models.Food.is_available == True).all()

    return foods



"""Flow for adding to cart:
1️⃣ Check user exists(user mot found checks)
2️⃣ Check user verified(user not verified checks)
3️⃣ Check food exists(food not found checks)
4️⃣ Check food availability(food unavailable checks)
5️⃣ Check quantity(quantity must be greater than zero checks)
6️⃣ Get user cart(cart not found checks)
7️⃣ Check if item already in cart(Duplicate cart item checks)
8️⃣ If exists, update quantity(Add new quantity to existing quantity)
9️⃣ If not, create new cart item(Add new item to cart)"""

@router.post("/cart/add")
def add_to_cart(data: schemas.cartAdd, db: Session = Depends(get_db)):

    # 1️⃣ Check user exists
    user = db.query(models.User).filter(
        models.User.id == data.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # 2️⃣ Check user verified
    if not user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="User not verified"
        )

    # 3️⃣ Check food exists
    food = db.query(models.Food).filter(
        models.Food.id == data.food_id
    ).first()

    if not food:
        raise HTTPException(
            status_code=404,
            detail="Food not found"
        )

    # 4️⃣ Check food availability
    if not food.is_available:
        raise HTTPException(
            status_code=400,
            detail="Food is currently unavailable"
        )

    # 5️⃣ Check quantity
    if data.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than zero"
        )

    # 6️⃣ Get user cart
    cart = db.query(models.Cart).filter(
        models.Cart.user_id == user.id
    ).first()

    if not cart:
       cart = models.Cart(
        user_id=user.id,
       )
       db.add(cart)
       db.commit()
       db.refresh(cart)

    # 7️⃣ Check if item already in cart
    existing_item = db.query(CartItem).filter(
    CartItem.cart_id == cart.id,
    CartItem.food_id == food.id
).first()

    if existing_item:
        new_total_quantity = existing_item.quantity + data.quantity

        if new_total_quantity > food.stock:
            raise HTTPException(
                status_code=400,
                detail="Not enough stock available"
            )

        existing_item.quantity = new_total_quantity

    else:
        if data.quantity > food.stock:
            raise HTTPException(
                status_code=400,
                detail="Not enough stock available"
            )


        new_item = models.CartItem(
            cart_id=cart.id,
            food_id=food.id,
            quantity=data.quantity,
            )
        db.add(new_item)
            
    db.commit()

    return {"message": "Item added to cart"}

@router.delete("/cart/item")
def remove_cart_item(
    user_id: int,
    food_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.food_id == food_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not in cart")

    db.delete(item)
    db.commit()

    return {"message": "Item removed from cart"}

@router.put("/cart/update")
def update_cart_quantity(
    user_id: int,
    food_id: int,
    quantity: int,
    db: Session = Depends(get_db)
):
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.food_id == food_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if quantity > item.food.stock:
        raise HTTPException(status_code=400, detail="Not enough stock available")

    item.quantity = quantity

    db.commit()

    return {"message": "Cart updated successfully"}

@router.delete("/cart/clear")
def clear_cart(
    user_id: int,
    db: Session = Depends(get_db)
):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()

    if not cart:
        return {"message": "Cart already empty"}

    for item in cart.items:
        db.delete(item)

    db.commit()

    return {"message": "Cart cleared"}


@router.get("/cart")
def get_cart(
    user_id: int,
    db: Session = Depends(get_db)
    ):
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_verified:
        raise HTTPException(status_code=400, detail="User not verified")


    cart = db.query(models.Cart).filter(
        models.Cart.user_id == user.id
    ).first()

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    if not cart.items:
        return {
            "items": [],
            "total": 0
        }

    items_response = []
    total = 0

    for item in cart.items:
        subtotal = item.food.price * item.quantity
        total += subtotal

        items_response.append({
            "food_name": item.food.name,
            "price": item.food.price,
            "quantity": item.quantity,
            "subtotal": subtotal
        })

    return {
        "items": items_response,
        "total": total
    }

"""System must:
Check user exists
Check verified
Check no existing pending order
Get cart
If empty → error
Validate stock for ALL items
Compute total
Create Order (status = "pending")
Create OrderItems
Reduce stock
Commit
All inside one transaction."""

@router.post("/order/create")
def create_order(
    user_id: int,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_verified:
        raise HTTPException(
            status_code=400, 
            detail="User not verified")

    existing_order = db.query(Order).filter(
    Order.user_id == user.id,
    Order.status == "pending").first()

    if existing_order:
        raise HTTPException(
            status_code=400,
            detail="You already have a pending order"
        )

    cart = db.query(Cart).filter(Cart.user_id == user.id).first()

    if not cart or not cart.items:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty"
        )

    for item in cart.items:
        if item.quantity > item.food.stock:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {item.food.name}"
            )

    total = 0
    for item in cart.items:
        total += item.food.price * item.quantity

    new_order = Order(
    user_id=user.id,
    total_price=total,
    status="pending"
    )

    db.add(new_order)
    db.flush()

    for item in cart.items:
        order_item = OrderItem(
            order_id=new_order.id,
            food_id=item.food.id,
            quantity=item.quantity,
            price_at_purchase=item.food.price
        )

        db.add(order_item)
    db.commit()

    return {
    "message": "Order created successfully",
    "order_id": new_order.id,
    "total_price": total,
    "status": new_order.status
    }

"""CANCEL ORDER LOGIC
This endpoint must:
Check user exists
Check verified
Find the order
Ensure it belongs to that user
Ensure status is "pending"
Restore stock
Change status to "cancelled"
Commit
We do NOT delete the order.
We just change status."""

@router.post("/order/cancel")
def cancel_order(
    user_id: int,
    order_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_verified:
        raise HTTPException(status_code=400, detail="User not verified")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if order.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Only pending orders can be cancelled"
        )

    for item in order.items:
        item.food.stock += item.quantity

    order.status = "cancelled"

    db.commit()

    return {
        "message": "Order cancelled successfully",
        "order_id": order.id,
        "status": order.status
    }

"""POST /pay
Logic Flow:

Get order
Check order exists
Check order status is pending
Create payment record
Mark order as paid
Reduce stock (if not already reduced)
Clear cart
Return receipt"""

@router.post("/pay")
def pay_for_order(
    user_id: int,
    order_id: int,
    payment_method: str,
    db: Session = Depends(get_db)
):
    import uuid

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "paid":
        raise HTTPException(status_code=400, detail="Order already paid")

    # 🔥 RECHECK STOCK BEFORE PAYMENT
    for item in order.items:
        if item.food.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for {item.food.name}"
            )

    # 🔥 REDUCE STOCK PERMANENTLY
    for item in order.items:
        item.food.stock -= item.quantity
    total = 0
    for item in order.items:
        total += item.quantity * item.price_at_purchase
        

    # Create payment
    payment = Payment(
        order_id=order.id,
        user_id=user_id,
        payment_method=payment_method,
        transaction_ref=str(uuid.uuid4()),
        amount=total,
        status="success"
    )

    db.add(payment)

    # Mark order as paid
    order.status = "paid"

    # Clear cart
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if cart:
        for item in cart.items:
            db.delete(item)

    db.commit()

    # 🔥 BUILD RECEIPT RESPONSE
    purchased_items = []

    for item in order.items:
        purchased_items.append({
            "food_name": item.food.name,
            "quantity": item.quantity,
            "price_per_unit": item.price_at_purchase,
            "subtotal": item.quantity * item.price_at_purchase
        })

    return {
        "message": "Payment successful",
        "transaction_reference": payment.transaction_ref,
        "order_id": order.id,
        "items_paid_for": purchased_items,
        "total_paid": payment.amount,
        "status": "paid"
    }
