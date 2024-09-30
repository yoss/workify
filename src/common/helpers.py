
from django.utils.safestring import mark_safe

class Breadcrumbs:
    def __init__(self):
        self.items = []

    def add(self, text, url=None, active=False, badge=None):
        """
        Adds a breadcrumb to the list.

        :param text: The display text for the breadcrumb.
        :param url: The URL the breadcrumb should link to.
        :param active: Whether the breadcrumb is the current/active page.
        :param badge: A badge to display next to the breadcrumb.
        """
        breadcrumb = {
            'text': text,
            'url': url,
            'active': active,
            'badge': badge
        }
        self.items.append(breadcrumb)

    # @classmethod
    # def create(cls, text, url=None, active=False):
    #     """
    #     Creates an instance of Breadcrumbs with the first breadcrumb already added.

    #     :param text: The display text for the breadcrumb.
    #     :param url: The URL the breadcrumb should link to.
    #     :param active: Whether the breadcrumb is the current/active page.
    #     :param badge: A badge to display next to the breadcrumb.
    #     """

    #     breadcrumbs = cls()
    #     breadcrumbs.add(text, url, active)
    #     return breadcrumbs
    
    def __iter__(self):
        """
        Allows iteration over breadcrumb items in a template.
        """
        # return iter(self.items)
        iterator = iter(self.items)
        last_item = None
        
        # Keep track of the previous item and the current item
        try:
            # Iterate through all items except the last one
            prev_item = next(iterator)
            for item in iterator:
                yield prev_item  # Yield the current item (not the last one)
                prev_item = item

            # Apply additional logic to the last element
            last_item = prev_item
            yield self.mark_last_element(last_item)

        except StopIteration:
            # Handle the case where the list is empty
            return

    def mark_last_element(self, last_item):
        """
        Marks the last breadcrumb item as active and deactivates url.
        """
        last_item['active'] = True
        last_item['url'] = None
        return last_item
    
# class Button():
#     def __init__(self, text, url, css_class, type = 'link', icon='link-2', target='_self', size = 'btn-sm'):
#         """
#         Creates a button object.
        
#         :param text: The display text for the button.
#         :param url: The URL the button should link to.
#         :param css_class: The CSS class to apply to the button. "btn-" class sufix from Bootstrap 5, if "outline-" profix is provided outline class wqill be added to both text buttoin and icon, if standard class will be added (e.g. 'primary), the class will be added to icon button, and outline version will be added to text button.
#         :param type: The type of button to create ('link', 'popup', 'submit', 'popup cancel', 'htmx'). Defaults to 'link'.
#         :param icon: The icon to display next to the button text. Defaults to 'link-2'.
#         :param target: The target (or hx-target) attribute for the button. Defaults to '_self'.
#         :param size: The size of the button. Defaults to 'btn-sm'.
#         """

#         if type not in ['link', 'popup', 'submit', 'submit2', 'popup cancel', 'htmx']:
#             raise ValueError("Button type must be 'link', 'popup', 'submit' or 'popup cancel'.")
        
#         # if target not in ['_self', '_blank']:
#         #     raise ValueError("Button target must be '_self' or '_blank'.")
        
#         button_classes = ["primary", "secondary", "success", "danger", "warning", "info", "light", "dark"]
#         outline_classes = ["outline-primary", "outline-secondary", "outline-success", "outline-danger", "outline-warning", "outline-info", "outline-light", "outline-dark"]

#         if css_class not in button_classes and css_class not in outline_classes:
#             raise ValueError("Button class must be a valid Bootstrap 5 button class sufix.")
#         if icon:
#             self.icon_class = css_class
#             if css_class in outline_classes:
#                 self.text_class = css_class
#             if css_class in button_classes:
#                 self.text_class = f"outline-{css_class}"

#         if icon is None:
#             self.text_class = css_class

#         self.text = text
#         self.url = url
#         self.type = type
#         self.icon = icon
#         self.target = target
#         self.size = '' if size is None or size == '' else size

    

class BaseButton():
    btn_css_clesses = ["primary", "secondary", "success", "danger", "warning", "info", "light", "dark"]
    btn_outline_css_clesses = ["outline-primary", "outline-secondary", "outline-success", "outline-danger", "outline-warning", "outline-info", "outline-light", "outline-dark"]
    hx_tags = " "
    bs_tags = " "
    form = False

    def __init__(self, text, css_class, icon, size):
        self.validate_css_class(css_class)
        self.validate_size(size)
        margin = "me-2" if icon is None else " "

        self.icon = icon
        self.text = text
        self.icon_css_class = self.get_icon_css_class(icon, css_class, size)
        self.text_css_class = f"btn btn-{css_class} {size} {margin}"
        
    def get_icon_css_class(self, icon, css_class, size):
        if icon is None:
            return ""
        if "outline-" in css_class:
            css_class = css_class.replace("outline-", "")
        return f"btn btn-{css_class} {size}"

    def validate_css_class(self, css_class):
        if css_class not in self.btn_css_clesses and css_class not in self.btn_outline_css_clesses:
            raise ValueError("Button class must be a valid Bootstrap 5 button class sufix.")

    def validate_size(self, size):
        if size not in ['btn-sm', 'btn-lg', None]:
            raise ValueError("Button size must be 'btn-sm', 'btn-lg' or None.")

class Buttons():
    class HtmxGet(BaseButton):
        def __init__(self, text, url, css_class, target, icon=None, size = 'btn-sm'):
            """
            Initialize a button with specific attributes for handling HTMX GET requests.

            Args:
                text (str): The text to display on the button.
                url (str): The URL to send HTMX GET request to.
                css_class (str): The CSS class (Bootstrap 5) to apply to the button.
                target (str): The target element to update with the GET response.
                icon (str, optional): The icon (Feather) to display on the button. Defaults to None.
                size (str, optional): The size (Bootstrap 5) of the button. Defaults to 'btn-sm'.
            """

            super().__init__(text, css_class, icon, size)
            self.open_tag = mark_safe("button type='button'")
            self.url = mark_safe(f"hx-get='{url}'")
            self.hx_tags = mark_safe(f"hx-target='{target}' hx-swap='innerHTML'  hx-trigger='click'")
            self.close_tag = "button"

    class Link(BaseButton):
        def __init__(self, text, url, css_class, target="_self", icon=None, size = 'btn-sm'):
            super().__init__(text, css_class, icon, size)
            self.open_tag = mark_safe("a ")
            self.url = mark_safe(f"href='{url}' target='{target}'")
            self.close_tag = "a"

    class ShowPopup(HtmxGet):
        def __init__(self, text, url, css_class, target="#PopupModalContent", icon=None, size = 'btn-sm'):
            super().__init__(text, url, css_class, target, icon, size)
            self.hx_tags = mark_safe(f"hx-target='{target}' hx-swap='innerHTML'  hx-trigger='click' hx-get='{url}'")
            self.bs_tags = mark_safe("data-bs-toggle='modal' data-bs-target='#PopupModal'")

    class HidePopup(BaseButton):
        def __init__(self, text, css_class, icon=None, size = 'btn-sm'):
            super().__init__(text, css_class, icon, size)
            self.open_tag = mark_safe("button type='button'")
            self.bs_tags = mark_safe("data-bs-dismiss='modal'")
            self.close_tag = "button"
            
    class PostCall(BaseButton):
        def __init__(self, text, url, css_class, icon=None, size = 'btn-sm'):
            super().__init__(text, css_class, icon, size)
            self.form = True
            self.action = url
            self.open_tag = mark_safe("button type='submit'")
            self.close_tag = "button"
            
    class SubmitForm(BaseButton):
        def __init__(self, text,css_class, icon=None, size = 'btn-sm'):
            super().__init__(text, css_class, icon, size)
            self.open_tag = mark_safe("button type='submit'")
            self.close_tag = "button"