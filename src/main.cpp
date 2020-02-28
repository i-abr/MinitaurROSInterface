/*
MIT License (modified)

Copyright (c) 2018 Ghost Robotics
Author: Avik De <avik@ghostrobotics.io>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this **file** (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
 */
#include <stdio.h>
#include <SDK.h>
#include <Motor.h>
#include <unistd.h>

#pragma pack(push, 1)
// Custom data to append to ethernet packet. No more than GRM_USER_DATA_SIZE=32 bytes!
struct UserData
{
	uint8_t bytes[GRM_USER_DATA_SIZE];
};
#pragma pack(pop)

uint32_t ethRxUpdated;

typedef struct _Command {
    float m[4];
    float l[4];
} Command;

class CommandOverEthernet : public Behavior
{
public:

    // Our received behaviorCmd and user data
	// BehaviorCmd behaviorCmd;
    Command joint_cmd;
	UserData data;

	void begin(){
        // Command limbs
        C->mode = RobotCommand_Mode_LIMB;
        // behaviorCmd.twist.linear.x = 1.0;
        for (int i = 0; i < 4; i ++) {
            joint_cmd.l[i] = 0.14;
            joint_cmd.m[i] = 0.;
        }
	}


	void update()
	{

    		// If no data, stop the robot
    		if(S->millis > ethRxUpdated + 2000) {// If it's too long past last time we received a packet
    			// Stop and re-enable the joystick
				// C->behavior.mode = 0;
				// C->behavior.twist.linear.x = 0;
                ;
    		}
    		else {
    			// Read BehaviorCmd from ethernet
    			int numRead = read(ETH_UPSTREAM_FILENO, &joint_cmd, sizeof(Command));
    			if(numRead == sizeof(Command)) {
    				// If sensible command
    				// if(behaviorCmd.id < 10 && behaviorCmd.mode < 10 &&
    				//    behaviorCmd.twist.linear.x <= 0.18 && behaviorCmd.twist.linear.x >= 0.12)
    				// {
                        for (int i = 0; i < P->limbs_count; ++i){
                            // Set limb type
                            P->limbs[i].type = LimbParams_Type_SYMM5BAR_EXT_M;

                            // Set leg angle gain and positon
                            limb[i].setGain(ANGLE, 0.8, 0.03);
                            limb[i].setPosition(ANGLE, joint_cmd.m[i]);

                            // Set leg extension gain and position
                            limb[i].setGain(EXTENSION, 120, 4);
                            limb[i].setPosition(EXTENSION, joint_cmd.l[i]);
                        }
                        // This is giving me errors so I am going to turn it off
						// Copy to behavior
						// memcpy(&C->behavior, &behaviorCmd, sizeof(BehaviorCmd));
    				// }
    			} else {
                    // Calculate leg angle value
                    // Use the negative pitch of the robot to keep the leg pointing down
                    float angle = -S->imu.euler.y;

                    // For all legs
                    for (int i = 0; i < P->limbs_count; ++i) {
                        // Set limb type
                        P->limbs[i].type = LimbParams_Type_SYMM5BAR_EXT_M;

                        // Set leg angle gain and positon
                        limb[i].setGain(ANGLE, 0.8, 0.03);
                        limb[i].setPosition(ANGLE, angle);

                        // Set leg extension gain and position
                        limb[i].setGain(EXTENSION, 120, 4);
                        limb[i].setPosition(EXTENSION, 0.15);
                    }
                }
            }

		// Create example user bytes to send back to computer
		for (int i = 0; i < GRM_USER_DATA_SIZE; ++i)
		{
			data.bytes[i] = i;
		}
		write(ETH_UPSTREAM_FILENO, &data, sizeof(UserData));

		// Send state happens automatically
	}
    void end() {

	}
};

CommandOverEthernet commandRobot;

// You can optionally send back a fully custom state packet by replacing the state copy callback.
// If you do this, don't write user bytes using the example user bytes above.
uint16_t myStateCopyCallback(GRMHeader *hdr, uint8_t *buf)
{
	hdr->version = 123;
	for (int i=0; i<10; ++i)
		buf[i] = i;
	return 10;
}

void debug()
{
	// Look at the last time we received from ethernet
	ioctl(ETH_UPSTREAM_FILENO, IOCTL_CMD_GET_LAST_UPDATE_TIME, &ethRxUpdated);
	//printf("%lu\t%d\t%d\n", ethRxUpdated, commandRobot.behaviorCmd.id, commandRobot.behaviorCmd.mode);
}

int main(int argc, char *argv[])
{
	// Only for Minitaur E
	init(RobotParams_Type_MINITAUR_E, argc, argv);

	// Set joystick, going to use it to switch modes
    // JoyType joyType = JoyType_FRSKY_XSR;
    JoyType joyType = JoyType_NONE;
	ioctl(JOYSTICK_FILENO, IOCTL_CMD_JOYSTICK_SET_TYPE, &joyType);

    // clear all the bound and walk behaviors
    behaviors.clear();

    behaviors.push_back(&commandRobot);
	// Create controller peripheral
    commandRobot.begin();

	// Add it
	// addPeripheral(&commandRobot);

	// Replace state copy callback
	//ioctl(ETH_UPSTREAM_FILENO, IOCTL_CMD_STATE_COPY_CALLBACK, (void *)myStateCopyCallback);

	// Remove bound behavior from Minitaur (first element of behaviors vector),
	// so we're left with only walk behavior
	// behaviors.erase(behaviors.begin());

	// Set debug rate
	setDebugRate(300);

	// Go
	return begin();
}
