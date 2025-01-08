# easyVFR2FG
This tool allows you to import an EasyVFR CSV export of a log book and replay it (more or less accurately) in FlightGear.

Export your logbook in CSV format (there's an example of export in this file).

Add these two parameters to FG (I use the launcher):

```
--generic=socket,in,60,localhost,49003,udp,input_log
--fdm=null
```

Run flightgear and make sure that you point the HOST in the .py file to the proper IP address.

Have fun!
