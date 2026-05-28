# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class DictPos(models.Model):
    id_pos = models.AutoField(primary_key=True)
    name_pos = models.TextField(db_column='Name_pos', db_collation='C')  # Field name made lowercase. This field type is a guess.

    class Meta:
        managed = False
        db_table = 'Dict_pos'


class DictServ(models.Model):
    id_serv = models.AutoField(primary_key=True)
    domen = models.TextField(blank=True, null=True)
    discription = models.TextField(blank=True, null=True)
    date_start = models.DateField()
    date_end = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Dict_serv'


class Dictapplic(models.Model):
    id_applic = models.AutoField(primary_key=True)
    app_name = models.TextField()
    app_type = models.TextField()
    app_disc = models.TextField(blank=True, null=True)
    data_begin = models.DateField()
    date_end = models.DateField(blank=True, null=True)
    id_server = models.ForeignKey(DictServ, models.DO_NOTHING, db_column='id_server')

    class Meta:
        managed = False
        db_table = 'Dictapplic'


class GroupD(models.Model):
    id_group = models.AutoField(primary_key=True)
    name = models.TextField(db_column='Name', db_collation='C')  # Field name made lowercase. This field type is a guess.
    id_app = models.ForeignKey(Dictapplic, models.DO_NOTHING, db_column='id_app')
    opption = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'Group_d'


class RoleD(models.Model):
    id_role = models.AutoField(primary_key=True)
    name = models.TextField(db_column='Name')  # Field name made lowercase.
    discription = models.TextField(blank=True, null=True)
    id_group = models.ForeignKey(GroupD, models.DO_NOTHING, db_column='id_group')
    date_begin = models.DateField()
    date_end = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Role_d'


class UserList(models.Model):
    id_user = models.AutoField(primary_key=True)
    id_pos = models.ForeignKey(DictPos, models.DO_NOTHING, db_column='id_pos')
    prizvische = models.TextField(db_column='Prizvische', db_collation='C')  # Field name made lowercase. This field type is a guess.
    name = models.TextField(db_column='Name', db_collation='C')  # Field name made lowercase. This field type is a guess.
    father_name = models.TextField(db_column='Father_Name', db_collation='C')  # Field name made lowercase. This field type is a guess.
    date_begin = models.DateField()
    date_end = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'User_list'

class UserRole(models.Model):
    # Додаємо primary_key=True та related_name
    id_role = models.ForeignKey('RoleD', models.DO_NOTHING, db_column='id_role', primary_key=True)
    id_user = models.ForeignKey('UserList', models.DO_NOTHING, db_column='id_user', related_name='userrole_set')

    class Meta:
        managed = False
        db_table = 'User_role'
        unique_together = (('id_role', 'id_user'),)
