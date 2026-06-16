import schemdraw
import schemdraw.elements as elm

with schemdraw.Drawing() as d:
    # VCC:
    vcc = d.add(elm.Vdd().label('VCC (+5V)'))
    dot0 = d.add(elm.Dot())
    
    ### INNER LEFT BRANCH:
    start_inner_left_branch = d.add(elm.Line().left().length(1.5))
    dot_il_1 = d.add(elm.Dot())
    r_led_il = d.add(elm.Resistor().down().label('1.1kΩ'))
    led_il = d.add(elm.LED().label('LED 3'))
    dot_il_2 = d.add(elm.Dot())
    end_inner_left_branch = d.add(elm.Line().right().length(1.5))

    ### MID LEFT BRANCH:
    start_mid_left_branch = d.add(elm.Line().at(dot_il_1.start).left().length(3))
    dot_ml_1 = d.add(elm.Dot())
    r_led_ml = d.add(elm.Resistor().down().label('1.1kΩ'))
    led_ml = d.add(elm.LED().label('LED 2'))
    dot_ml_2 = d.add(elm.Dot())
    end_mid_left_branch = d.add(elm.Line().right().length(3))

    ### OUTER LEFT BRANCH:
    start_outer_left_branch = d.add(elm.Line().at(dot_ml_1.start).left().length(3))
    dot_ol_1 = d.add(elm.Dot())
    r_led_ol = d.add(elm.Resistor().down().label('5.1kΩ'))
    led_ol = d.add(elm.LED().label('LED 1'))
    dot_ol_2 = d.add(elm.Dot())
    end_outer_left_branch = d.add(elm.Line().right().length(3))


    ### OUTER OUTER LEFT BRANCH:
    start_outer_outer_left_branch = d.add(elm.Line().at(dot_ol_1.start).left().length(3))
    r_led_ool = d.add(elm.Resistor().down().label('5.1kΩ'))
    led_ool = d.add(elm.LED().label('LED 0'))
    end_outer_outer_left_branch = d.add(elm.Line().right().length(3))
    

    ### INNER RIGHT BRANCH:
    start_inner_right_branch = d.add(elm.Line().right().at(dot0.start).length(1.5))
    dot_ir_1 = d.add(elm.Dot())
    r_led_ir = d.add(elm.Resistor().down().label('1.1kΩ'))
    led_ir = d.add(elm.LED().down().label('LED 4'))
    dot_ir_2 = d.add(elm.Dot())
    end_inner_right_branch = d.add(elm.Line().left().at(led_ir.end).length(1.5))


    ### MID RIGHT BRANCH:
    start_mid_right_branch = d.add(elm.Line().right().at(dot_ir_1.start).length(3))
    dot_mr_1 = d.add(elm.Dot())
    r_led_mr = d.add(elm.Resistor().down().label('1.1kΩ'))
    led_mr = d.add(elm.LED().down().label('LED 5'))
    dot_mr_2 = d.add(elm.Dot())
    end_mid_branch = d.add(elm.Line().left().at(led_mr.end).length(3))


    ### OUTER RIGHT BRANCH:
    start_outer_right_branch = d.add(elm.Line().right().at(dot_mr_1.start).length(3))
    dot_or_1 = d.add(elm.Dot())
    r_led_or = d.add(elm.Resistor().down().label('5.1kΩ'))
    led_or = d.add(elm.LED().down().label('LED 6'))
    dot_or_2 = d.add(elm.Dot())
    end_outer_branch = d.add(elm.Line().left().at(led_or.end).length(3))

    ### OUTER RIGHT BRANCH:
    start_outer_outer_right_branch = d.add(elm.Line().right().at(dot_or_1.start).length(3))
    dot_oor_1 = d.add(elm.Dot())
    r_led_oor = d.add(elm.Resistor().down().label('5.1kΩ'))
    led_oor = d.add(elm.LED().down().label('LED 7'))
    dot_oor_2 = d.add(elm.Dot())
    end_outer_outer_branch = d.add(elm.Line().left().at(led_oor.end).length(3))


    ### ELKO:
    start_elko = d.add(elm.Line().right().at(dot_oor_1.start).length(3))
    elko_line_1 = d.add(elm.Line().down().length(1.5))
    elko = d.add(elm.Capacitor().down().label('100µF'))
    elko_line_2 = d.add(elm.Line().down().length(1.5))
    end_elko = d.add(elm.Line().left().at(elko_line_2.end).length(3))
    
    
    # MERGE:
    merge = d.add(elm.Dot().at(end_inner_left_branch.end))

    # TRANSISTOR:
    transistor_in = d.add(elm.Line().down().length(0.5))
    transistor = d.add(elm.BjtNpn().anchor("collector").right())

    # GND:
    gnd = d.add(elm.Ground().at(transistor.emitter))
    
    # GPIO:
    r0 = d.add(elm.Resistor().left().at(transistor.base).label('1.1kΩ'))
    gpio = d.add(elm.Dot(open=True).label('GPIO', 'left'))
