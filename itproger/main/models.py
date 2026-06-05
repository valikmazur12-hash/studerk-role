from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    id_dep = models.AutoField(primary_key=True)
    name_dep = models.CharField(max_length=150, default="Служба інформаційних технологій")

    class Meta:
        db_table = 'Department'

class DictPos(models.Model):
    id_pos = models.AutoField(primary_key=True)
    name_pos = models.CharField(max_length=150, db_column='Name_pos')

    class Meta:
        db_table = 'Dict_pos'

class DictServ(models.Model):
    id_serv = models.AutoField(primary_key=True)
    domen = models.CharField(max_length=255, blank=True, null=True)
    discription = models.TextField(blank=True, null=True)
    date_start = models.DateField()
    date_end = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'Dict_serv'

class Dictapplic(models.Model):
    id_applic = models.AutoField(primary_key=True)
    app_name = models.CharField(max_length=150)
    app_type = models.CharField(max_length=100)
    app_disc = models.TextField(blank=True, null=True)
    data_begin = models.DateField()
    date_end = models.DateField(blank=True, null=True)
    id_server = models.ForeignKey(DictServ, on_delete=models.CASCADE, db_column='id_server')

    class Meta:
        db_table = 'Dictapplic'

class GroupD(models.Model):
    id_group = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150, db_column='Name')
    id_app = models.ForeignKey(Dictapplic, on_delete=models.CASCADE, db_column='id_app')
    opption = models.IntegerField()

    class Meta:
        db_table = 'Group_d'

class RoleD(models.Model):
    id_role = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150, db_column='Name')
    discription = models.TextField(blank=True, null=True)
    id_group = models.ForeignKey(GroupD, on_delete=models.CASCADE, db_column='id_group')
    date_begin = models.DateField()
    date_end = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'Role_d'

class UserList(models.Model):
    id_user = models.AutoField(primary_key=True)
    id_pos = models.ForeignKey(DictPos, on_delete=models.PROTECT, db_column='id_pos')
    id_dep = models.ForeignKey(Department, on_delete=models.PROTECT, db_column='id_dep', default=1)
    
    # Зв'язок 1-до-1, який ми щойно налаштували в pgAdmin через auth_user_id
    auth_user = models.OneToOneField(User, on_delete=models.CASCADE, db_column='auth_user_id', related_name='user_profile', null=True, blank=True)
    
    prizvische = models.CharField(max_length=100, db_column='Prizvische')
    name = models.CharField(max_length=100, db_column='Name')
    father_name = models.CharField(max_length=100, db_column='Father_Name')
    date_begin = models.DateField()
    date_end = models.DateField(blank=True, null=True)

    class Meta:
        db_table = 'User_list'

class UserRole(models.Model):
    """ Проміжна таблиця зв'язку користувачів та ролей без помилки унікальності ролі """
    id = models.AutoField(primary_key=True) 
    id_role = models.ForeignKey(RoleD, on_delete=models.CASCADE, db_column='id_role')
    id_user = models.ForeignKey(UserList, on_delete=models.CASCADE, db_column='id_user', related_name='userrole_set')

    class Meta:
        db_table = 'User_role'
        unique_together = (('id_role', 'id_user'),) 