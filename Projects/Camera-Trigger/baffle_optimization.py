"""
Optimal Baffle Wave Analysis for ToF Cone
Computes the best sine wave parameters to minimize light bounce
"""
import math

# Cone parameters
cone_height = 43.0  # mm
top_radius = 12.8   # mm (outer)
half_angle = 13.5   # degrees (27° FOV / 2)
wall_thickness = 1.0  # mm

# Inner radii
inner_top_radius = top_radius - wall_thickness
delta_r = cone_height * math.tan(math.radians(half_angle))
inner_bottom_radius = max(inner_top_radius - delta_r, 0.5)

print('=' * 60)
print('OPTIMAL BAFFLE WAVE ANALYSIS FOR TOF CONE')
print('=' * 60)
print(f'Cone height: {cone_height}mm')
print(f'Inner top radius: {inner_top_radius:.1f}mm')
print(f'Inner bottom radius: {inner_bottom_radius:.1f}mm')
print(f'FOV half-angle: {half_angle}°')
print()


def analyze_wave_params(amplitude, wavelength, cone_height, half_angle):
    """
    Analyze how well wave parameters trap stray light.
    
    For a sine wave: y = A * sin(2π * z / λ)
    The derivative: dy/dz = A * (2π/λ) * cos(2π * z / λ)
    Max slope occurs at zero crossings: max_slope = 2πA/λ
    """
    # Maximum slope angle of the sine wave surface
    max_slope = 2 * math.pi * amplitude / wavelength
    max_slope_angle = math.degrees(math.atan(max_slope))
    
    # Stray light angles to block: anything > FOV half-angle
    # Typical stray angles: 15° to 60° from vertical
    stray_angles = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
    
    trap_scores = []
    for stray_angle in stray_angles:
        # For light at angle θ hitting a surface tilted at φ:
        # - If surface slope ≥ θ, light can be redirected downward into cone
        # - Light reflects at angle 2φ - θ from vertical
        # - We want reflected light to hit another surface (not exit)
        
        if max_slope_angle >= stray_angle:
            # Surface steep enough to redirect this ray downward
            trap_scores.append(1.0)
        elif max_slope_angle >= stray_angle * 0.7:
            # Partial redirection - some rays trapped
            trap_scores.append(0.7)
        elif max_slope_angle >= stray_angle * 0.5:
            trap_scores.append(0.5)
        else:
            # Surface too shallow - ray bounces back out
            trap_scores.append(0.2)
    
    avg_trap = sum(trap_scores) / len(trap_scores)
    num_waves = cone_height / wavelength
    
    # Printability constraints for FDM:
    # - Wavelength ≥ 2mm (nozzle can't resolve finer)
    # - Amplitude 0.3-1.5mm (too small = invisible, too large = weak walls)
    # - Waves 8-20 (enough to trap, not too many to print)
    printable = (wavelength >= 2.0 and 
                 amplitude >= 0.3 and 
                 amplitude <= 1.5 and
                 num_waves >= 6 and 
                 num_waves <= 25)
    
    return {
        'amplitude': amplitude,
        'wavelength': wavelength,
        'num_waves': num_waves,
        'max_slope_angle': max_slope_angle,
        'trap_efficiency': avg_trap,
        'printable': printable
    }


def ray_trace_analysis(amplitude, wavelength, cone_height, inner_top_r, inner_bottom_r):
    """
    Simple ray tracing to count bounces for stray light.
    """
    # Simulate rays entering at various angles
    entry_angles = [20, 30, 40, 50]  # degrees from vertical
    bounces_needed = []
    
    for angle in entry_angles:
        # Ray enters from top, travels down at angle
        # Each time it hits a wave surface, it bounces
        # Count bounces until ray exits bottom or is absorbed
        
        ray_angle = math.radians(angle)
        z = 0  # Start at top
        bounces = 0
        
        while z < cone_height and bounces < 10:
            # Distance to next wave peak/trough
            wave_period = wavelength
            dz = wave_period / 4  # Hit surface every quarter wavelength
            
            # Surface slope at this point (varies sinusoidally)
            phase = (z / wavelength) * 2 * math.pi
            surface_slope = (2 * math.pi * amplitude / wavelength) * math.cos(phase)
            surface_angle = math.atan(surface_slope)
            
            # Reflection: new_angle = 2 * surface_angle - ray_angle
            ray_angle = 2 * surface_angle - ray_angle
            
            # Clamp to reasonable range
            ray_angle = max(-math.pi/2, min(math.pi/2, ray_angle))
            
            z += dz
            bounces += 1
        
        bounces_needed.append(bounces)
    
    return sum(bounces_needed) / len(bounces_needed)


print('WAVE PARAMETER OPTIMIZATION')
print('-' * 60)
print(f'{"Amp(mm)":<9} {"λ(mm)":<8} {"Waves":<7} {"Slope°":<8} {"Trap%":<7} {"Bounces":<8} {"OK"}')
print('-' * 60)

results = []

for amp in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0, 1.2]:
    for wavelength in [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]:
        result = analyze_wave_params(amp, wavelength, cone_height, half_angle)
        avg_bounces = ray_trace_analysis(amp, wavelength, cone_height, 
                                         inner_top_radius, inner_bottom_radius)
        result['avg_bounces'] = avg_bounces
        
        # Combined score: trap efficiency * bounce count * printability
        score = result['trap_efficiency'] * min(avg_bounces, 6) / 6
        if result['printable']:
            score *= 1.2  # Bonus for printability
        if 10 <= result['num_waves'] <= 18:
            score *= 1.1  # Bonus for optimal wave count
        
        result['score'] = score
        results.append(result)
        
        status = '✓' if result['printable'] else '✗'
        trap_pct = result['trap_efficiency'] * 100
        print(f'{amp:<9.1f} {wavelength:<8.1f} {result["num_waves"]:<7.1f} '
              f'{result["max_slope_angle"]:<8.1f} {trap_pct:<7.0f} {avg_bounces:<8.1f} {status}')

# Find best printable result
printable_results = [r for r in results if r['printable']]
best = max(printable_results, key=lambda x: x['score'])

print('-' * 60)
print()
print('=' * 60)
print('OPTIMAL PARAMETERS')
print('=' * 60)
print(f'  Amplitude:       {best["amplitude"]:.1f} mm')
print(f'  Wavelength:      {best["wavelength"]:.1f} mm')
print(f'  Wave count:      {best["num_waves"]:.0f} waves')
print(f'  Max slope:       {best["max_slope_angle"]:.1f}°')
print(f'  Trap efficiency: {best["trap_efficiency"]*100:.0f}%')
print(f'  Avg bounces:     {best["avg_bounces"]:.1f}')
print()

print('PHYSICS EXPLANATION')
print('-' * 60)
print(f'• Stray light enters at angles > {half_angle}° from vertical')
print(f'• Sine wave max slope = arctan(2πA/λ) = {best["max_slope_angle"]:.1f}°')
print(f'• Steeper slopes redirect more rays into the cone')
print(f'• {best["num_waves"]:.0f} wave cycles = {best["num_waves"]:.0f} chances to absorb')
print(f'• Matte black PLA absorbs ~15% per bounce')
print(f'• After {best["avg_bounces"]:.0f} bounces: ~{(1-0.85**best["avg_bounces"])*100:.0f}% absorbed')
print()

# Convert to Fusion units (cm)
amp_cm = best['amplitude'] / 10
wl_cm = best['wavelength'] / 10
num_waves = int(round(best['num_waves']))

print('=' * 60)
print('FUSION 360 VALUES (in cm)')
print('=' * 60)
print(f'  wave_amplitude = {amp_cm:.2f}   # {best["amplitude"]:.1f}mm')
print(f'  num_waves = {num_waves}')
print(f'  # wavelength = cone_height / num_waves = {cone_height/10/num_waves:.3f}cm')
print()
print('Copy these values to update the cone!')
