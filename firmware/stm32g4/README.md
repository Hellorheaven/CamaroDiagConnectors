# STM32G474 development firmware

Prototype only, all proposed target pins high impedance, no actuator, SPI bus or vehicle connection. Use only an isolated NUCLEO-G474RE board via ST-LINK USB. Build: `pio run -d firmware/stm32g4`. The serial output is a diagnostic heartbeat, not proof of physical interlock or authenticated device state. The board must be electrically qualified before any interprocessor or ECU cable is attached. PlatformIO board reference: https://docs.platformio.org/en/stable/boards/ststm32/nucleo_g474re.html.
