window.addEventListener("load", () => {
    const tg = window.Telegram.WebApp,
          USER_CHAT_ID = tg.initDataUnsafe.chat.id;

    tg.expand();

    const set_close_event = () => {
        document.querySelectorAll(".close_app").forEach((item, index, arr) => {
            item.addEventListener("click", () => {
                tg.close();
            })
        })
    }
    set_close_event()

    localStorage.clear()

    let date_input_grid = document.querySelector("#date-input-grid"),
        main_app_header = document.querySelector("#main-app-header"),
        start_date_input = document.querySelector("#start-date-input"),
        end_date_input = document.querySelector("#end-date-input")
    
    main_app_header.classList.add("animate__bounceIn")
    date_input_grid.classList.add("animate__bounceIn")

    let submit_date_period_btn = document.querySelector("#submit-date-period"),
        operations_display_grid = document.querySelector("#operations-display-grid"),
        operations_display_p = document.querySelector("#operations-display-p"),
        table_choose_grid = document.querySelector("#table-choose-grid")

    const show_preloaders = () => {
        let preloaders = document.querySelectorAll(".preloader")
        preloaders.forEach((item, index, arr) => {
            item.classList.remove("d-none")
            item.parentElement.disabled = true
        })
    }

    const close_preloaders = () => {
        let preloaders = document.querySelectorAll(".preloader")
        preloaders.forEach((item, index, arr) => {
            item.classList.add("d-none")
            item.parentElement.disabled = false
        })
    }

    const error_handler = (error) => {
        let error_handler_block = document.querySelector("#error-handler"),
            error_handler_text = document.querySelector("#error-handler-span")

        const close_modal = () => {
            error_handler_block.classList.remove("animate__bounceIn")
            error_handler_block.classList.add("animate__bounceOut")
            setTimeout(() => {
                error_handler_block.classList.add("d-none")
                error_handler_block.classList.remove("animate__bounceOut")
            }, 500)

        }

        if(error_handler_block.classList.contains("d-none")){
            error_handler_text.textContent = error

            error_handler_block.classList.remove("d-none")
            error_handler_block.classList.add("animate__bounceIn")
        }else{
            close_modal()
            error_handler_text.textContent = error
            setTimeout(() => {
                error_handler_block.classList.remove("d-none")
                error_handler_block.classList.add("animate__bounceIn")
            }, 1000)
        }

        document.querySelector("#error-handler-close").addEventListener("click", () => close_modal())
        setTimeout(close_modal, 5000)
    }

    submit_date_period_btn.addEventListener("click", async (event) => {
        event.preventDefault();

        localStorage.start_date = start_date_input.value,
        localStorage.end_date = end_date_input.value
        
        if((start_date_input.value.trim() == "") || (end_date_input.value.trim() == "")){
            return error_handler("Заполните поля ниже.")
        
        }else if ((new Date(start_date_input.value) == "Invalid Date") || (new Date(end_date_input.value) == "Invalid Date")){
            start_date_input.value = ""
            end_date_input.value = ""

            return error_handler("Некорректные даты.")
        
        }else if (new Date(start_date_input.value) > new Date(end_date_input.value)){
            start_date_input.value = ""
            end_date_input.value = ""

            return error_handler("Конечная дата не может быть меньше начальной.")
        
        }else{
            localStorage.start_date = start_date_input.value,
            localStorage.end_date = end_date_input.value
        
            // получаем таблицы пользователя
            const params = new URLSearchParams()
            params.append("user_chat_id", USER_CHAT_ID)

            show_preloaders()
            await axios.post(
                "/accounting/webapp/api/get_user_tables",
                params
            ).then((response) =>{
                if(response.status == 200){
                    user_tables = response.data.data
                    console.log("%cТаблицы пользователя получены.", "color:green;font-size:large")
                    
                    close_preloaders()

                    for (let index = 0; index < user_tables.length; index++) {
                        const table = user_tables[index];

                        table_choose_grid.innerHTML += `
                            <div class="d-grid gap-2 mt-3 category-analysis-wrapper">
                                <button type="button" class="btn btn-outline-secondary btn-table-choose" id="table_${table.table_id}">
                                    <span class="spinner-border spinner-border-sm preloader d-none" role="status" aria-hidden="true"></span>
                                    ${table.table_name}
                                </button>
                            </div>
                        `
                    }

                    table_choose_grid.innerHTML += `
                        <div class="d-grid gap-2 mt-4 category-analysis-wrapper">
                            <button type="button" class="btn btn-danger close_app">Закрыть приложение ❌</button>
                        </div>
                    `

                    date_input_grid.classList.remove("animate__bounceIn")
                    date_input_grid.classList.add("animate__bounceOut")
                    
                    setTimeout(() => {
                        date_input_grid.classList.add("d-none")
                        table_choose_grid.classList.remove("d-none")
                        table_choose_grid.classList.add("animate__bounceIn")
                    }, 1000)
                    
                    active_table_buttons()
                    set_close_event()

                }else{
                    close_preloaders()

                    return error_handler("Ошибка запроса.")
                }
            }).catch((error) => {
                console.error(`Ошибка запроса.\n${error}`)
                close_preloaders()

                return error_handler("Ошибка запроса")
            })
        }
    })

    const active_table_buttons = () => {
        let btn_table_choose = document.querySelectorAll(".btn-table-choose")

        btn_table_choose.forEach((item, index, arr) => {
            item.addEventListener("click", async () => {
                
                show_preloaders()

                const params = new URLSearchParams(),
                      active_table_id = item.id.split("_").slice(-1)[0]

                params.append("user_chat_id", USER_CHAT_ID)
                params.append("start_date", localStorage.start_date)
                params.append("end_date", localStorage.end_date)
                params.append("table_id", active_table_id)

                await axios.post(
                    "/accounting/webapp/api/get_user_operations",
                    params
                ).then((response) => {
                    if(response.status == 200){
                        localStorage.active_table_id = active_table_id
                        const operations_wrapper = document.querySelector("#operations-wrapper"),
                              operations = response.data.operations,
                              money_info = response.data.money_info

                        for (let index = 0; index < operations.length; index++) {
                            const operation = operations[index];
                                  
                            operations_wrapper.innerHTML += `
                                    <div class="accordion-item" id="operation_${operation.id}"> 
                                    <h2 class="accordion-header" id="heading_${operation.id}">
                                    <button class="accordion-button collapsed list-group-item d-flex justify-content-between align-items-center" type="button" data-bs-toggle="collapse" data-bs-target="#collapse_${operation.id}" aria-expanded="false" aria-controls="collapse_${operation.id}">
                                        <div class="row list-item-wrapper">
                                            <div class="col-4 d-flex align-items-center justify-content-center">
                                                <p class="operation-date m-0">${operation.date}</p>
                                            </div>
                                            <div class="col-4 d-flex align-items-center justify-content-center">
                                                <p class="operation-amount m-0">${operation.amount}₽</p>
                                            </div>
                                            <div class="col-4 d-flex align-items-center justify-content-center">
                                                <p class="operation-type m-0">${operation.type}</p>
                                        </div>
                                    </button>
                                    </h2>
                                    <div id="collapse_${operation.id}" class="accordion-collapse collapse" aria-labelledby="heading_${operation.id}" data-bs-parent="#operations-wrapper">
                                    <div class="accordion-body">
                                        <strong>Описание:</strong><p>${operation.description != null ? operation.description : "У вас нет описания для данной операции🥴"}</p>
                                        <strong>Категория:</strong><p>${operation.category}</p>
                                        
                                        <div class="d-grid gap-2 mt-3 category-analysis-wrapper">
                                            <button type="button" class="btn btn-outline-danger delete-operation-btn" id="delete_button_${operation.id}">
                                            <span class="spinner-border spinner-border-sm preloader d-none" role="status" aria-hidden="true"></span>
                                                Удалить 🚮
                                            </button>
                                        </div>
                                    </div>
                                    </div>
                                </div>
                            `
                        }

                        operations_wrapper.innerHTML += `
                            <p class="form-text-primary m-0 mt-2">Доход:<span class="text-success" id="period-income">${money_info.total_income}₽</span></p>
                            <p class="form-text-primary m-0">Расход:<span class="text-danger" id="period-consumption">${money_info.total_consumption}₽</span></p>
                            <p class="form-text-primary m-0">Расход:<span class="text-warning" id="period-profit">${money_info.total_profit}₽</span></p>
                        `
                        
                        set_close_event()
                        close_preloaders()

                        document.querySelectorAll(".delete-operation-btn").forEach((item, index, arr) => {
                            item.addEventListener("click", async () => {
                                if(confirm("Вы действительно хотите удалить запись?")){
                                    show_preloaders()
                                    const params = new URLSearchParams(),
                                          operation_id = item.id.split("_").pop()

                                    params.append("user_chat_id", USER_CHAT_ID)
                                    params.append("operation_id", operation_id)

                                    await axios.post("/accounting/webapp/api/delete_user_operations", params)
                                    .then((response) => {
                                        if(response.status == 200){
                                            document.querySelector(`#operation_${operation_id}`).remove()
                                            alert("Операция успешно удалена.")
                                            close_preloaders()

                                        }else{
                                            close_preloaders()
                                            return error_handler("Ошибка запроса")
                                        }
                                            
                                        
                                    })
                                    .catch((error) => {
                                        close_preloaders()

                                        console.error(`Ошибка запроса.\n${error}`)
                                        return error_handler("Ошибка запроса")
                                    })

                                }
                            })
                        })

                        table_choose_grid.classList.remove("animate__bounceIn")
                        table_choose_grid.classList.add("animate__bounceOut")

                        period = `${localStorage.start_date.split("-").reverse().join(".")} по ${localStorage.end_date.split("-").reverse().join(".")}`
                        operations_display_p.innerHTML = `Ваши операции за период <b>${period}</b>`  

                        setTimeout(() => {
                            table_choose_grid.classList.add("d-none")
                            operations_display_grid.classList.remove("d-none")
                            operations_display_grid.classList.add("animate__bounceIn")
                        }, 1000)

                    }else{
                        close_preloaders()
                        return error_handler("Ошибка запроса")
                    }
                }).catch((error) => {
                    close_preloaders()

                    console.error(`Ошибка запроса.\n${error}`)
                    return error_handler("Ошибка запроса")
                })
            })
        })
    }



})

