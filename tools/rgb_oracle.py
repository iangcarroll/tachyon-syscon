"""Execute original RGB and soft-float code; hook only PWM and timer endpoints."""
from oracle import Oracle


class RgbOracle(Oracle):
    STATE=0x200003a8

    def __init__(self,state=bytes(28),timer_result=0):
        super().__init__()
        self.put(self.STATE,state)
        self.events=[]
        self.timer_result=timer_result
        self.hooks.update({0x87dc:self._pwm_init,0x88c0:self._pwm_write,
                           0x781c:self._register,0x776c:self._timer_init,
                           0x8f88:self._timer_error})

    def _pwm_init(self,o):
        self.events.append(('pwm-init',o.arg(0)))

    def _pwm_write(self,o):
        self.events.append(('pwm-write',o.arg(0),o.arg(1)))

    def _register(self,o):
        self.events.append(('register',o.arg(0),o.arg(1),o.arg(2),o.arg(3)))
        return self.timer_result

    def _timer_init(self,o):
        self.events.append(('timer-init',))

    def _timer_error(self,o):
        self.events.append(('timer-error',))

    def state(self):
        return bytes(self.cpu.mem_read(self.STATE,28))
