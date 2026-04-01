# FreeRTOS

!!! Abstract "摘要"
    这篇文章是对 FreeRTOS 学习的引入，介绍了为什么需要使用RTOS，以及 RTOS 的设计理念。

### 主循环

很多人写代码经常会使用这样的写法：
```c
void vButtonTask()
{
	
}

void vUartTask()
{

}

void vAdcTask()
{
	
}

void vTask(){
	vButtonTask();
	vUartTask();
	vAdcTask();
}

int main(){
	
	while(1){
		vTask();
	}
}
```

这是一种**顺序**的写法，在主循环中处理。这样能够完成任务。但是，一旦任务耗时较长（中间有Delay，比如按键的延时消抖，串口发送的阻塞，ADC采样的耗时）就会造成相应不灵敏等问题。

### 定时器中断+主循环

要改进这种写法，可以使用经典的前后台的写法，使用**主循环加定时器中断**。将时间计数放在定时器中断里，每隔1ms产生一次中断。
- 为每一个任务定义三个变量： `task_cnt` `task_flag` `task_cnt_threshold`
- 在定时器中断中，每次进入中断按顺序做下面的事
	- 计数增加1 `task_cnt++` 
	- 判断是否到达阈值： `if(task >= threshold)`
	- 如果到达阈值，将 `task_cnt = 0`，并且将 `task_flag = 1` 提醒任务可以开始了。
- 任务函数放在主循环中，每次进入任务函数，判断 `task_flag` 是否为1，如果为1，则执行任务，并且在任务最后设置为0。

经过以上的流程，就能够实现一个任务每隔一段时间执行一次。这是我在写裸机项目的时候最常用的写法。

只是这种写法还是存在缺点，如果任务本身就会花费不少时间（比如ADC采样时间较长），那么这个问题依旧没法解决。在大家 flag 都为1的情况下依然需要排队等待那个时间长的任务先执行。那么按键的反应依旧会变慢（但是比之前好）。

### 操作系统的引入

如何解决这个问题，就要引出操作系统的设计理念：

!!! important "操作系统的理念"
    - **时间片轮转**：对于相同优先级任务，交替执行（并发）。这样不会出现像按键那样耗时短的任务被耗时长的任务阻塞这种事情。
    - **抢占式调度**：对于不同优先级的任务，高优先级任务能打断低优先级的任务。

使用 FreeRTOS 之后，就会发现ADC（等效于delay）不会在主循环中阻塞其他任务，串口打印时间时间也基本准确。但是如何让时间更准确呢？

这里提供一种方法：
```c
void vUartTask()
{
    uint32_t ulBeginTime;  //ul 指的是 unsigned long
    
    // 1. 获取任务开始时刻
    ulBeginTime = HAL_GetTick();
    
    // 2. 执行串口打印
    printf("uart time:%d \n\r", HAL_GetTick());
    
    // 3. 延时到 ulBeginTime + 1000ms 时刻
    vTaskDelayUntil(&ulBeginTime, 1000);
}
```

使用这种方式就可以精确的延时一段时间，而不会被任务执行的时间所干扰。


!!! quote "参考视频"
    【【江科大】江科大老学长带你 FreeRTOS 工程项目实践】https://www.bilibili.com/video/BV1nvqSBAELQ