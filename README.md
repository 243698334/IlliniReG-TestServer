IlliniReG-Server
================

Class registration helper for University of Illinois at Urbana-Champaign, including an Availability Monitor and a Register Machine.

## Description

  A simple server handles client requests of monitoring/registering classes.
  Notifications will be send when a seat is found or class is registered. Currently it provides SMS and email.
  Records are kept in a MySQL database.

## TODO

  lecture and discussion simultaneous monitoring/registering  
  user signup  
  store password securely  
  data sync between client and server  
  push database schema  
  package setup script  
  
  And of course, I’ll be working on a client with a friendly UI.

## Dependencies

   libpynexmo  
   mechanize  
   MySQLdb  
