# Terminology

## UI elements

UI elements refer to graphical user interfaces that is used to construct an application. Currently, chatbots aren't that great in understanding natural language and this is the reason for UI elements to exist in messaging apps. You can think UI elements as a buttons,  forms, check-boxes, etc.



![screenshot of form](images/screenshot_checkbox.form.jpg)

## Fallback Value

This values are derived either from third party API's or users profile.  

For example, if user says *"Nearby ATMs"*. In this example, the user has not provided any information about his location in the chat but, we can pass a *fallback_value* that will contain its location that can be obtained from its profile or third party APIs (like geopy, etc).

