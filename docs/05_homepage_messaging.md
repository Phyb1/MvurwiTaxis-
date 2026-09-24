# Homepage messaging recommendation

## Current
Taxis available in Mvurwi

## Recommended passenger-facing hero
Find a Taxi in Mvurwi

## Recommended supporting text
Browse local taxi drivers, check availability, and contact a driver directly.

## CTA
Request Any Taxi →

## Add a small driver CTA near the hero or below the driver list
Are you a taxi driver in Mvurwi?
List your taxi →  Start free

## Why
The homepage is primarily a passenger product. "Find a Taxi in Mvurwi" is clearer as a task-oriented headline than "Taxis available in Mvurwi." Keep the driver recruitment message secondary so the passenger journey remains obvious.

## Suggested template change
<h1>Find a Taxi in Mvurwi</h1>
<p class="hero-copy">Browse local taxi drivers, check availability, and contact a driver directly.</p>
<p><a href="{% url 'taxis:request_taxi' %}" class="btn-wa" style="display:inline-block;width:auto;">Request Any Taxi &rarr;</a></p>
<p class="driver-cta">Are you a taxi driver? <a href="{% url 'taxis:driver_signup' %}">List your taxi</a></p>

Note: confirm the actual URL name for driver signup in your project before copying the last line. If the route name differs, use the existing List Your Taxi URL.
