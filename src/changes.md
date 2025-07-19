# 📊 Changes


### Dashboard

1. `/dashboard/student/list/`  
   - 🔑 **key**:  `by_code` ➝ `is_center`


2. `/dashboard/student/rest-password/<username>/`  
   - 🔁 **Method**: `POST` ➝ `PATCH`


3. `/dashboard/student/change-center-status/`  
   - 🔁 **Method**: `POST` ➝ `PATCH`


4. `/dashboard/student/details/<student id>/`
    - 🔑 **key**:  `by_code` ➝ `is_center`


5. `/dashboard/admin/create-admin`
    - 🟢 **url**: `/dashboard/staff/create/`


6. `/dashboard/admin/list`
    - 🟢 **url**: `/dashboard/staff/list/`


7. `/dashboard/admin/profile/`
    - 🟢 **url**: `/dashboard/staff/profile/`


8. `/dashboard/course/list`
    - 🔑 **key**:  `center` ➝ `is_center`
    - 🔑 **key**:  `lessons_count` ➝ `videos_count`
    - ➕🔑 **add**:  `can_buy`


9. `/dashboard/course/details/<course id>`
    - 🔑 **key**:  `center` ➝ `is_center`
    - 🔑 **key**:  `lessons_count` ➝ `videos_count`
    - ➕🔑 **add**:  `can_buy`


10. `/dashboard/course/create`
    - 🔑 **key**:  `center` ➝ `is_center`
    - ➕🔑 **add**:  `can_buy`
    


11. `/dashboard/courses/update/<course id>`
    - 🟢 **url**: `/dashboard/course/update/<course id>/`
    - 🔑 **key**:  `center` ➝ `is_center`


12. `/dashboard/courses/delete/<course id>`
    - 🟢 **url**: `/dashboard/course/delete/<course id>/`


13. `/dashboard/unit/list/<course id>`
    - 🟢 **url**: `/dashboard/course/unit/list/<course id>/`
    - ➕🔑 **add**: `subunits`



14. `/dashboard/unit/create/<course id>`
    - 🟢 **url**: `/dashboard/course/unit/create/<course id>/`
    - ➕ **add**: `pagination`
    - ➕🔑 **add**: `parent`
    - ➕🔑 **add**: `price`


15. `/dashboard/unit/update/<unit id>`
    - 🟢 **url**: `/dashboard/course/unit/update/<unit id>/`
    - ➕🔑 **add**: `parent`
    - ➕🔑 **add**: `price`


16. `/dashboard/unit/content/<int:unit_id>`
    - 🟢 **url**: `/dashboard/course/unit/content/<unit id>/`
    - **Lesson**
        - 🔑 **key**:  `content_type : lesson ` ➝ `content_type : video `
        - 🔑 **key**:  `video_duration` ➝ `duration`
        - 🔑 **key**:  `lesson_files` ➝ `video_files`
        - 🔑 **key**:  `view` ➝ `can_view`
        - ❌🔑 **key**: `video_url`
        - ❌🔑 **key**: `youtube_url`
        - ❌🔑 **key**: `vdocipher_id`
        - ➕ 🔑 **key**: `publisher_date`
        - ➕ 🔑 **key**: `stream_type` *(Choices)*
            1. easystream_encrypt
            2. easystream_not_encrypted
            3. youtube_hide
            4. youtube_show
            5. vdocipher
            6. vimeo
        - ➕ 🔑 **key**: `stream_link`
        - ➕ 🔑 **key**: `can_buy`
    

17. `/dashboard/lesson/list/<int:unit_id>`
    - 🟢 **url**: `/dashboard/unit/video/list/<int:unit_id>/`
    - 🔑 **key**:  `content_type : lesson ` ➝ `content_type : video `
    - 🔑 **key**:  `video_duration` ➝ `duration`
    - 🔑 **key**:  `lesson_files` ➝ `video_files`
    - 🔑 **key**:  `view` ➝ `can_view`
    - ❌🔑 **key**: `video_url`
    - ❌🔑 **key**: `youtube_url`
    - ❌🔑 **key**: `vdocipher_id`
    - ➕ 🔑 **key**: `publisher_date`
    - ➕ 🔑 **key**: `stream_type` *(Choices)*
        1. easystream_encrypt
        2. easystream_not_encrypted
        3. youtube_hide
        4. youtube_show
        5. vdocipher
        6. vimeo
    - ➕ 🔑 **key**: `stream_link`
    - ➕ 🔑 **key**: `can_buy`


18. `/dashboard/lesson/create/<int:unit_id>`
    - 🟢 **url**: `/dashboard/unit/video/create/<int:unit_id>/`
    - 🔑 **key**:  `view` ➝ `can_view`
    - 🔑 **key**:  `lesson_files` ➝ `video_files`
    - ➕ 🔑 **key**: `publisher_date`
    - ➕ 🔑 **key**: `stream_type`
        1. easystream_encrypt
        2. easystream_not_encrypted
        3. youtube_hide
        4. youtube_show
        5. vdocipher
        6. vimeo

    - ➕ 🔑 **key**: `stream_link`
    - ➕ 🔑 **key**: `can_buy`
    - ➕ 🔑 **key**: `free`
    - ❌🔑 **key**: `video_url`
    - ❌🔑 **key**: `youtube_url`
    - ❌🔑 **key**: `vdocipher_id`


19. `/dashboard/lesson/update/<int:lesson_id>`
    - 🟢 **url**: `/dashboard/video/update/<int:video id>/`
    - 🔑 **key**:  `view` ➝ `can_view`
    - 🔑 **key**:  `lesson_files` ➝ `video_files`
    - ➕ 🔑 **key**: `publisher_date`
    - ➕ 🔑 **key**: `stream_type`
        1. easystream_encrypt
        2. easystream_not_encrypted
        3. youtube_hide
        4. youtube_show
        5. vdocipher
        6. vimeo

    - ➕ 🔑 **key**: `stream_link`
    - ➕ 🔑 **key**: `can_buy`
    - ❌🔑 **key**: `video_url`
    - ❌🔑 **key**: `youtube_url`
    - ❌🔑 **key**: `vdocipher_id`



19. `/dashboard/lesson/delete/<lesson id>`
    - 🟢 **url**: `/dashboard/video/delete/<int:video id>/`



20. `/dashboard/lesson-file/list/<lesson id>`
    - 🟢 **url**: `/dashboard/video/file/list/<video id>/`


21. `/dashboard/lesson-file/create/<lesson id>`
    - 🟢 **url**: `/dashboard/video/file/create/<video id>/`


22. `/dashboard/lesson-file/delete/<file id>`
    - 🟢 **url**: `/dashboard/video/file/delete/<file id>/`


23. `/dashboard/file/list/<unit id>`
    - 🟢 **url**: `/dashboard/unit/file/list/<unit id>/`


24. `/dashboard/file/create/<unit id>`
    - 🟢 **url**: `/dashboard/unit/file/create/<unit id>/`

25. `/dashboard/content-details/<int:course_id>/<str:content_type>/<content id>`
    - 🟢 **url**:`content-details/<str:content_type>/<content id>/`


26. `/dashboard/invoice/list/`
    - ❌🔑 **key**: `course__name`
    - ❌🔑 **key**: `course__price`
    - ❌🔑 **key**: `course_collection__name`
    - ❌🔑 **key**: `course_collection__price`
    - ❌🔑 **key**: `lesson__name`
    - ❌🔑 **key**: `lesson__price`
    - ❌🔑 **key**: `free`
    - ➕🔑 **key**: `item_price`
    - ➕🔑 **key**: `item_name`
    - ➕🔑 **key**: `item_barcode`
    - ➕🔑 **key**: `item_type`
        - video
        - course
    - 🔑 **key**: `price` ➝ `amount`
    - 🔑 **key**: `pay_status`
        - paid
        - failed
        - expired
    - 🔑 **key**: `pay_method`
        - code
        - easy_pay
        - free


27. ```
    - /dashboard/course-category/list/
    - /dashboard/course-category/create/
    - /dashboard/course-category/update/<int:id>/
    - /dashboard/course-category/delete/<int:id>/
    ```
    - 🟢 **url**:
        ```
            - /dashboard/course/category/list/
            - /dashboard/course/category/create/
            - /dashboard/course/category/update/<int:id>/
            - /dashboard/course/category/delete/<int:id>/
        ```


28. `/dashboard/unit/content/resort-content/<int:unit_id>`
    - 🟢 **url**: `/dashboard/content/resort/`


29. `/dashboard/unit/resort-units/<int:course_id>/`
    - 🟢 **url**: `/dashboard/course/unit/resort/`


30. `/dashboard/unit/copy-unit/`
    - 🟢 **url**: `/dashboard/course/unit/copy/`


31. `/dashboard/subscription/cancel/bulk/`
    - 🟢 **url**: `/dashboard/subscription/cancel-bulk/`

32. `/dashboard/subscription/subscription-many-student`
    - 🟢 **url**: `/dashboard/subscription/start/bulk/`


33. `/dashboard/subscription/renew-subscription/<int:subscription_id>`
    - 🟢 **url**: `/dashboard/subscription/renew/<int:subscription_id>/`


34. `/dashboard/codes/generate-course-codes`
    - 🟢 **url**: `/dashboard/codes/course/generate/`

35. `/dashboard/codes/generate-lesson-codes`
    - 🟢 **url**: `/dashboard/codes/video/generate/`


35. `/dashboard/codes/course-code-list`
    - 🟢 **url**: `/dashboard/codes/course/list/`


35. `/dashboard/codes/video-code-list`
    - 🟢 **url**: `/dashboard/codes/video/list/`


### Student

1. `/student/student-profile`
    - 🟢 **url**: `/student/profile/`
    - 🔑 **key**:  `by_code` ➝ `is_center`


2. `/student/student-sign-up`
    - 🟢 **url**: `/student/sign-up/`


4. `/student/student-sign-in`
    - 🟢 **url**: `/student/sign-in/`


5. `/student/student-sign-code`
    - 🟢 **url**: `/student/sign-center-code/`


6. `student/student-token-refresh`
    - 🟢 **url**: `/student/token-refresh/`


### Course

1. `/course/course-categories-list`
    - 🟢 **url**: `/course/categories/list/`

2. `/course/course-list`
    - 🟢 **url**: `/course/list/`
    - 🔑 **key**:  `center` ➝ `is_center`
    - 🔑 **key**:  `course_id` ➝ `id`
    - ➕🔑 **add**:  `can_buy`
    - ➕🔑 **add**: `barcode`
    - ➕ **add**: `pagination`
    - ➕🔑 **add**:  `can_buy`



3. `/course/course-details/<course id>`
    - 🟢 **url**: `/course/details/<course id>/`
    - 🔑 **key**:  `center` ➝ `is_center`
    - 🔑 **key**:  `course_id` ➝ `id`


### Unit
1. `/course/unit-list/<course id>`
    - 🟢 **url**: `course/unit/list/<course id>/`
    - ➕ **add**: `pagination`
    - ➕🔑 **add**: `subunits`


2. `/course/unit-content/<unit id>/`
    - 🟢 **url**: `/course/unit/content/<unit id>/`
    - **Lesson**
        - 🔑 **key**:  `video_duration` ➝ `duration`
        - 🔑 **key**:  `content_type : lesson ` ➝ `content_type : video `
        - 🔑 **key**:  `lesson_files_count` ➝ `video_files_count`
        - ➕🔑 **add**: `barcode`








X course__name
X course_collection__name    => item_name
X lesson__name


X course__price
X course_collection__price  => item_price
X lesson__price

