# rtl-sdr scanner and recorder

This project contains my rtl-sdr script written in `python3` to scan and record interesting frequencies. See video below for details.

[![YouTube video](http://img.youtube.com/vi/TSDbcb7wSjs/0.jpg)](http://www.youtube.com/watch?v=TSDbcb7wSjs "YouTube video")

## Prerequisites

You need some tools to start the work.

```
python3 python3-pip rtl-sdr sox
```

Install it before continue. For example on Debian based distribution run follow commands:
```
sudo apt-get install python3 python3-pip rtl-sdr sox
```

Clone the repository into your local machine. After that, install needed libraries.
```
pip3 install --user -r requirements.txt
```

## Configuration

Edit your configuration in file:
```
config.json
```

## Run

Run below commands in terminal to get help:
```
./sources/main.py --help
```
## Example
```
shajen@artemida:~/git/auto-sdr $ sources/main.py config.json -vvv -pbf 10 -fbf
[2020-03-31 13:35:23][   INFO][   sdr] 
[2020-03-31 13:35:23][   INFO][   sdr] ################################################################################
[2020-03-31 13:35:23][   INFO][   sdr] ############################# IGNORED FREQUENCIES ##############################
[2020-03-31 13:35:23][   INFO][   sdr] ################################################################################
[2020-03-31 13:35:23][   INFO][   sdr] ignored frequency range user defined: 28,799,000 Hz - 28,801,000 Hz
[2020-03-31 13:35:23][   INFO][   sdr] ignored frequency range user defined: 115,199,000 Hz - 115,201,000 Hz
[2020-03-31 13:35:23][   INFO][   sdr] ignored frequency range user defined: 438,470,000 Hz - 438,490,000 Hz
[2020-03-31 13:35:23][   INFO][   sdr] ignored frequency range user defined: 439,000,000 Hz - 439,010,000 Hz
[2020-03-31 13:35:23][   INFO][   sdr] 
[2020-03-31 13:35:23][   INFO][   sdr] ################################################################################
[2020-03-31 13:35:23][   INFO][   sdr] ############################### SCANNING RANGES ################################
[2020-03-31 13:35:23][   INFO][   sdr] ################################################################################
[2020-03-31 13:35:23][   INFO][   sdr] scanned frequency range: 26,000,000 Hz - 28,000,000 Hz
[2020-03-31 13:35:23][   INFO][   sdr] scanned frequency range: 28,000,000 Hz - 30,000,000 Hz
[2020-03-31 13:35:23][   INFO][   sdr] scanned frequency range: 50,000,000 Hz - 52,000,000 Hz
[2020-03-31 13:35:23][   INFO][   sdr] scanned frequency range: 108,000,000 Hz - 144,000,000 Hz
[2020-03-31 13:35:23][   INFO][   sdr] scanned frequency range: 144,000,000 Hz - 146,000,000 Hz
[2020-03-31 13:35:23][   INFO][   sdr] scanned frequency range: 430,000,000 Hz - 440,000,000 Hz
[2020-03-31 13:35:23][   INFO][   sdr] 
[2020-03-31 13:35:23][   INFO][   sdr] ################################################################################
[2020-03-31 13:35:23][   INFO][   sdr] ############################### SCANNING STARTED ###############################
[2020-03-31 13:35:23][   INFO][   sdr] ################################################################################
Found Rafael Micro R820T tuner
[R82XX] PLL not locked!
Exact sample rate is: 2000000.052982 Hz
[2020-03-31 13:35:30][   INFO][   sdr] start recording frequency: 144,498,046 Hz, power:  -4.16 dB #######################_________________
[2020-03-31 13:35:41][   INFO][   sdr] stop recording frequency: 144,498,046 Hz
[2020-03-31 13:35:42][   INFO][   sdr] recording time: 8.52 seconds
Found Rafael Micro R820T tuner
[R82XX] PLL not locked!
Exact sample rate is: 2000000.052982 Hz
[2020-03-31 13:35:43][  DEBUG][   sdr] frequency: 144,431,640 Hz, power:  -6.29 dB ###############_________________________
[2020-03-31 13:35:43][  DEBUG][   sdr] frequency: 144,497,558 Hz, power:  -6.33 dB ###############_________________________
[2020-03-31 13:35:43][  DEBUG][   sdr] frequency: 144,497,680 Hz, power:  -5.98 dB ################________________________
[2020-03-31 13:35:43][  DEBUG][   sdr] frequency: 144,497,802 Hz, power:  -5.80 dB #################_______________________
[2020-03-31 13:35:43][  DEBUG][   sdr] frequency: 144,497,924 Hz, power:  -4.76 dB #####################___________________
[2020-03-31 13:35:43][  DEBUG][   sdr] frequency: 144,498,046 Hz, power:  -4.16 dB #######################_________________
[2020-03-31 13:35:43][  DEBUG][   sdr] frequency: 144,498,168 Hz, power:  -4.17 dB #######################_________________
[2020-03-31 13:35:43][  DEBUG][   sdr] frequency: 144,498,291 Hz, power:  -4.77 dB #####################___________________
[2020-03-31 13:35:43][  DEBUG][   sdr] frequency: 144,498,413 Hz, power:  -5.83 dB #################_______________________
[2020-03-31 13:35:43][  DEBUG][   sdr] frequency: 144,498,535 Hz, power:  -6.01 dB ################________________________
[2020-03-31 13:35:43][  DEBUG][   sdr] --------------------------------------------------------------------------------
^C[2020-03-31 13:36:06][WARNING][killer] stopping application
```

All recorded frequencies are stored in `wav` directory.

## Contributing

In general don't be afraid to send pull request. Use the "fork-and-pull" Git workflow.

1. **Fork** the repo
2. **Clone** the project to your own machine
3. **Commit** changes to your own branch
4. **Push** your work back up to your fork
5. Submit a **Pull request** so that we can review your changes

NOTE: Be sure to merge the **latest** from **upstream** before making a pull request!

## Donations

If you enjoy this project and want to thanks, please use follow link:

[![Support via PayPal](https://www.paypalobjects.com/webstatic/en_US/i/buttons/pp-acceptance-medium.png)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=shajen@shajen.pl&lc=US&item_name=rtl+sdr+scanner&no_note=0&cn=&curency_code=USD)

## License

[![License](https://img.shields.io/:license-GPLv3-blue.svg?style=flat-square)](https://www.gnu.org/licenses/gpl.html)

- *[GPLv3 license](https://www.gnu.org/licenses/gpl.html)*
