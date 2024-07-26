from django.contrib.auth import get_user_model

def user_info(request):
    user = request.user
    if user.is_authenticated:
        user_data = {
            'username': user.username,
            'img':user.profile_img
         
            # Include other relevant user fields as needed
            
        }
        # print(f'profile image url is {user_data['img']}')
        return user_data
    else:
        return {}