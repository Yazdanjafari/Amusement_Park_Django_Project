from treebeard.mp_tree import MP_NodeQuerySet
from django.db import models


class CategoryQuerySet(MP_NodeQuerySet):
    def is_active(self):
        return self.filter(is_active=True)
    

class ProductModelManager(models.Manager):
    def all(self):
        # Customize the 'all' queryset here
        return super().filter(is_active=True)  # Call the default 'all' method