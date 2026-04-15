# 🚀 Sistema de Alertas de Trading - Binance + Telegram

Sistema automatizado que monitorea BTC y altcoins de baja capitalización en Binance, detecta cuando los precios se acercan a niveles de soporte/resistencia y envía alertas a Telegram.

## ✨ Características

- 📡 Conexión a API pública de Binance (sin necesidad de API keys)
- 📊 Análisis de al menos 10 monedas (BTC + 9 altcoins low-cap)
- 📈 Cálculo de soportes y resistencias semanales y mensuales
- 🔔 Detección de toques con margen de sensibilidad del 1%
- 🔥 Prioridad para alertas de BTC
- 📱 Notificaciones a Telegram
- ⏱️ Ejecución manual o automática cada 5 minutos
- 🎯 Enfoque en temporalidad de 4 horas para entradas

## 📋 Requisitos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Bot de Telegram (creado con BotFather)

## 🔧 Instalación

### 1. Clonar o descargar el proyecto

```bash
unzip crypto_alert_system.zip
cd crypto_alert_system