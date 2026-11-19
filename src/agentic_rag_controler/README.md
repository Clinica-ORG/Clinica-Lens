# Bugs encountered and solution
1. pydantic Validation error for User
- User id in Database in often in `UUID` format, if `user_id` in User model is `str`, we need to converted it into `string`
```python
User(user_id=str(user["id"]), name=user["user_name"], role=user["role"])
```